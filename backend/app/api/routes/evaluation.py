import json
from typing import Any, AsyncGenerator, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.models import (
    AgentRefinementResult,
    BatchRefineRequest,
    EvaluationRequest,
    EvaluationResponse,
    RefactorRequest,
    RefactorResponse,
    RefactorRunRequest,
    RefactorRunResponse,
)
from app.core.runner import get_chat_client, run_evaluation, run_evaluation_stream
from app.services.refactor_ingest import normalize_refactor_payload
from app.services.refactor_runtime import (
    apply_ground_truth_report_to_blueprint,
    build_ground_truth_assessment,
    run_blueprint_in_runtime,
)

router = APIRouter()


def _unwrap_request_envelope(payload: dict, envelope_keys: list[str]) -> dict:
    merged = dict(payload)
    for key in envelope_keys:
        nested = merged.get(key)
        if isinstance(nested, dict):
            unwrapped = dict(nested)
            for outer_key, outer_val in merged.items():
                if outer_key == key:
                    continue
                # Keep explicit top-level values only when nested does not define them.
                unwrapped.setdefault(outer_key, outer_val)
            return unwrapped
    return merged


def _coerce_json_string_to_dict(payload: Any, field_name: str, notes: List[str]) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if not isinstance(payload, str):
        return {"observed_output": str(payload)}

    text = payload.strip()
    if not text:
        return {}
    if text in {"{}", "''", '""'}:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        notes.append(f"{field_name} is not valid JSON; using safe fallback object so normalization can continue.")
        return {"observed_output": text}
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        return {"items": parsed}
    if parsed is None:
        return {}
    return {"value": parsed}


def _coerce_json_string_to_list(payload: Any, field_name: str, notes: List[str]) -> list[Any]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, tuple):
        return list(payload)
    if not isinstance(payload, str):
        return [payload]

    text = payload.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        notes.append(f"{field_name} is not valid JSON; treating as single-item text input list.")
        return [text]
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        if isinstance(parsed.get("items"), list):
            return parsed["items"]
        notes.append(f"{field_name} expected a list; wrapping dict into single-item list.")
        return [parsed]
    if parsed is None:
        return []
    return [str(parsed)]


def _sanitize_refactor_request_payload(payload: dict, notes: List[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        notes.append("Request payload was not an object; using empty fallback payload.")
        return {}

    normalized = dict(payload)

    candidate = normalized.get("payload")
    if isinstance(candidate, dict):
        merged = dict(candidate)
        for key, value in normalized.items():
            if key != "payload":
                merged.setdefault(key, value)
        normalized = merged
        notes.append("Applied top-level `payload` object wrapper.")
    elif isinstance(candidate, str):
        wrapped = _coerce_json_string_to_dict(candidate, "payload", notes)
        if wrapped:
            merged = dict(wrapped)
            for key, value in normalized.items():
                if key != "payload":
                    merged.setdefault(key, value)
            normalized = merged
            notes.append("Applied top-level `payload` string wrapper.")
        else:
            normalized["payload"] = candidate

    if isinstance(normalized.get("raw_payload"), (str, dict)):
        normalized["raw_payload"] = _coerce_json_string_to_dict(
            normalized.get("raw_payload"),
            "raw_payload",
            notes,
        )
    if isinstance(normalized.get("blueprint"), (str, dict)):
        normalized["blueprint"] = _coerce_json_string_to_dict(
            normalized.get("blueprint"),
            "blueprint",
            notes,
        )
    if isinstance(normalized.get("traces"), (str, list, dict)):
        normalized["traces"] = _coerce_json_string_to_list(
            normalized.get("traces"),
            "traces",
            notes,
        )
    if isinstance(normalized.get("test_cases"), (str, list, dict)):
        normalized["test_cases"] = _coerce_json_string_to_list(
            normalized.get("test_cases"),
            "test_cases",
            notes,
        )
    if isinstance(normalized.get("test_inputs"), (str, list, dict)):
        normalized["test_inputs"] = _coerce_json_string_to_list(
            normalized.get("test_inputs"),
            "test_inputs",
            notes,
        )

    return normalized


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "blueprint": {
                            "agent": {
                                "name": "my_agent",
                                "description": "Short description of what the agent does.",
                                "system_prompt": "You are a helpful assistant. Follow these steps: 1) Call the relevant tool. 2) Return a clear response to the user.",
                                "provider": "azure_openai",
                                "tools": [
                                    {
                                        "name": "my_tool",
                                        "description": "Does something useful.",
                                        "parameters": {
                                            "type": "object",
                                            "properties": {
                                                "query": {"type": "string"}
                                            },
                                            "required": ["query"]
                                        }
                                    }
                                ]
                            },
                            "test_cases": [
                                {
                                    "description": "Basic query test",
                                    "input": "User message sent to the agent",
                                    "expected_behavior": "Agent calls my_tool and returns a clear response."
                                }
                            ],
                            "evaluation_criteria": {
                                "goals": ["Always call the relevant tool", "Return a clear and accurate response"],
                                "constraints": ["Must not answer outside its domain"],
                                "priority_description": "Correct tool use is mandatory. A response without a tool call is a failure."
                            }
                        },
                        "traces": [
                            {
                                "timestamp": "2024-01-01T12:00:00",
                                "mode": "sequential",
                                "input": "User message sent to the agent",
                                "agents": {
                                    "my_agent": {
                                        "instructions": "You are a helpful assistant...",
                                        "tools_available": ["my_tool"],
                                        "tool_calls": [
                                            {
                                                "tool": "my_tool",
                                                "arguments": {"query": "some input"},
                                                "result": {"data": "some result"}
                                            }
                                        ],
                                        "output": "Here is the result based on the tool response.",
                                        "duration_ms": 1200
                                    }
                                },
                                "execution_order": ["my_agent"],
                                "handoffs": [],
                                "final_output": "Here is the result based on the tool response.",
                                "duration_ms": 1500
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate an AI agent against its blueprint and refine its system prompt if score < 0.7.
    Read the agent blueprint JSON file and pass as `blueprint`. Read all trace log JSON files and pass as the `traces` array.
    Pass `blueprint` and `traces` at the root level with no wrapper key.
    `provider` must be one of: azure_openai, openai, anthropic, mistral, grok — omit if unknown.
    Returns overall_score 0-1, per-test results, summary, and optionally a refined system prompt.
    """
    try:
        return await run_evaluation(request.blueprint, request.traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/Optimize",
    response_model=RefactorResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "from_genai_repo_snippets": {
                            "summary": "Flexible request with repo snippets only",
                            "value": {
                                "repo_files": [
                                    {"path": "README.md", "content": "# My Agent\n..."},
                                    {"path": "agent.py", "content": "SYSTEM_PROMPT='You are ...'"}
                                ],
                                "test_inputs": ["User asks for a summary"],
                                "agent_name": "repo_agent",
                            },
                        },
                        "from_existing_payload": {
                            "summary": "Single raw payload string from another GenAI tool",
                            "value": {
                                "raw_payload": "{\"system_prompt\":\"You are a coding assistant\",\"test_inputs\":[\"Refactor this file\"],\"observed_output\":\"Done\"}"
                            },
                        },
                    }
                }
            }
        }
    },
)
async def optimize(request: RefactorRequest) -> RefactorResponse:
    """
    Flexible endpoint for GenAI clients.
    Accepts partial or loosely formatted payloads and normalizes them into
    AgentBlueprint + TraceLog internally before running evaluation/refinement.
    """
    normalize_notes: List[str] = []
    payload = _sanitize_refactor_request_payload(
        _unwrap_request_envelope(
            request.model_dump(),
            ["RefactorRequest", "refactorRequest", "request", "payload"],
        ),
        normalize_notes,
    )
    try:
        blueprint, traces, notes = await normalize_refactor_payload(payload)
        notes = normalize_notes + notes
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Optimize payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to normalize Optimize payload: {exc}") from exc

    try:
        result = await run_evaluation(blueprint, traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Optimize evaluation failed: {exc}") from exc

    return RefactorResponse(
        evaluation=result.evaluation,
        refinement=result.refinement,
        judge_diagnostics=result.diagnostics,
        normalized_blueprint=blueprint if request.include_normalized_payload else None,
        normalized_traces_count=len(traces),
        normalization_notes=notes,
    )


@router.post("/Optimize-run", response_model=RefactorRunResponse)
async def optimize_run(request: RefactorRunRequest) -> RefactorRunResponse:
    """
    Runtime execution endpoint:
    1) Normalizes flexible input into blueprint/traces.
    2) Executes blueprint test cases to generate fresh runtime traces.
    3) Builds a ground-truth precheck report from expected_output/expected_behavior.
    4) Feeds augmented blueprint + traces into judge/refiner workflow.
    """
    normalize_notes: List[str] = []
    payload = _sanitize_refactor_request_payload(
        _unwrap_request_envelope(
            request.model_dump(),
            ["RefactorRunRequest", "refactorRunRequest", "request", "payload"],
        ),
        normalize_notes,
    )
    try:
        blueprint, normalized_traces, notes = await normalize_refactor_payload(payload, allow_github_url=False)
        notes = normalize_notes + notes
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Optimize-run payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to normalize Optimize-run payload: {exc}") from exc

    max_iterations = 3
    target_score = 0.9
    chat_client = get_chat_client()
    current_blueprint = blueprint
    last_generated_traces = []
    last_ground_truth_report: list[dict[str, Any]] = []
    last_traces_for_judge_count = 0
    result = None

    for iteration in range(1, max_iterations + 1):
        try:
            generated_traces, runtime_notes = await run_blueprint_in_runtime(
                current_blueprint,
                chat_client,
                max_test_cases=request.max_test_cases,
            )
            notes.extend([f"[iteration {iteration}] {note}" for note in runtime_notes])
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Runtime execution failed: {exc}") from exc

        ground_truth_report = build_ground_truth_assessment(current_blueprint, generated_traces)
        blueprint_for_judge = apply_ground_truth_report_to_blueprint(current_blueprint, ground_truth_report)

        traces_for_judge = list(generated_traces)
        if request.use_existing_traces:
            traces_for_judge.extend(normalized_traces)
            notes.append(
                f"[iteration {iteration}] Appended {len(normalized_traces)} normalized trace(s) to generated runtime traces."
            )

        try:
            result = await run_evaluation(blueprint_for_judge, traces_for_judge)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Optimize-run evaluation failed: {exc}") from exc

        last_generated_traces = generated_traces
        last_ground_truth_report = ground_truth_report
        last_traces_for_judge_count = len(traces_for_judge)
        score = result.evaluation.overall_score
        notes.append(f"[iteration {iteration}] Evaluation overall_score={score:.4f} (target >= {target_score:.2f}).")

        if score >= target_score:
            notes.append(f"Stopped after iteration {iteration}: target score reached.")
            break

        if iteration == max_iterations:
            notes.append(f"Stopped after iteration {iteration}: reached max iterations.")
            break

        if not result.refinement or not result.refinement.refined_prompt.strip():
            notes.append(f"Stopped after iteration {iteration}: no refined_prompt available for next rerun.")
            break

        next_blueprint_raw = current_blueprint.model_dump(mode="json")
        next_blueprint_raw["agent"]["system_prompt"] = result.refinement.refined_prompt
        current_blueprint = type(current_blueprint).model_validate(next_blueprint_raw)
        notes.append(f"[iteration {iteration}] Applied refined_prompt and reran runtime execution.")

    if result is None:
        raise HTTPException(status_code=500, detail="Optimize-run failed to produce an evaluation result.")

    return RefactorRunResponse(
        evaluation=result.evaluation,
        refinement=result.refinement,
        judge_diagnostics=result.diagnostics,
        normalized_blueprint=current_blueprint if request.include_normalized_payload else None,
        generated_traces=last_generated_traces if request.include_generated_traces else [],
        traces_used_count=last_traces_for_judge_count,
        ground_truth_report=last_ground_truth_report,
        normalization_notes=notes,
    )


@router.post("/refine-all-stream")
async def refine_all_stream(request: BatchRefineRequest) -> StreamingResponse:
    chat_client = get_chat_client()

    async def generate() -> AsyncGenerator[str, None]:
        for item in request.items:
            agent_name = item.blueprint.agent.name or "Unknown Agent"
            try:
                async for chunk in run_evaluation_stream(agent_name, item.blueprint, item.traces, chat_client):
                    yield chunk
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'detail': f'Error processing {agent_name}: {exc}'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/refine-all", response_model=List[AgentRefinementResult])
async def refine_all(request: BatchRefineRequest) -> List[AgentRefinementResult]:
    results: List[AgentRefinementResult] = []
    for item in request.items:
        try:
            response = await run_evaluation(item.blueprint, item.traces)
            results.append(AgentRefinementResult(
                agent_name=item.blueprint.agent.name or "Unknown Agent",
                evaluation=response.evaluation,
                refinement=response.refinement,
            ))
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Refinement failed for agent '{item.blueprint.agent.name}': {exc}",
            ) from exc
    return results
