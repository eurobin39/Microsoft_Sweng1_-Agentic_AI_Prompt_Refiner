import json
from typing import AsyncGenerator, List

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
    "/refactor",
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
async def refactor(request: RefactorRequest) -> RefactorResponse:
    """
    Flexible endpoint for GenAI clients.
    Accepts partial or loosely formatted payloads and normalizes them into
    AgentBlueprint + TraceLog internally before running evaluation/refinement.
    """
    try:
        blueprint, traces, notes = await normalize_refactor_payload(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid refactor payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to normalize refactor payload: {exc}") from exc

    try:
        result = await run_evaluation(blueprint, traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refactor evaluation failed: {exc}") from exc

    return RefactorResponse(
        evaluation=result.evaluation,
        refinement=result.refinement,
        normalized_blueprint=blueprint if request.include_normalized_payload else None,
        normalized_traces_count=len(traces),
        normalization_notes=notes,
    )


@router.post("/refactor-run", response_model=RefactorRunResponse)
async def refactor_run(request: RefactorRunRequest) -> RefactorRunResponse:
    """
    Runtime execution endpoint:
    1) Normalizes flexible input into blueprint/traces.
    2) Executes blueprint test cases to generate fresh runtime traces.
    3) Builds a ground-truth precheck report from expected_output/expected_behavior.
    4) Feeds augmented blueprint + traces into judge/refiner workflow.
    """
    try:
        blueprint, normalized_traces, notes = await normalize_refactor_payload(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid refactor-run payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to normalize refactor-run payload: {exc}") from exc

    chat_client = get_chat_client()
    try:
        generated_traces, runtime_notes = await run_blueprint_in_runtime(
            blueprint,
            chat_client,
            max_test_cases=request.max_test_cases,
        )
        notes.extend(runtime_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Runtime execution failed: {exc}") from exc

    ground_truth_report = build_ground_truth_assessment(blueprint, generated_traces)
    blueprint_for_judge = apply_ground_truth_report_to_blueprint(blueprint, ground_truth_report)

    traces_for_judge = list(generated_traces)
    if request.use_existing_traces:
        traces_for_judge.extend(normalized_traces)
        notes.append(f"Appended {len(normalized_traces)} normalized trace(s) to generated runtime traces.")

    try:
        result = await run_evaluation(blueprint_for_judge, traces_for_judge)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refactor-run evaluation failed: {exc}") from exc

    return RefactorRunResponse(
        evaluation=result.evaluation,
        refinement=result.refinement,
        normalized_blueprint=blueprint if request.include_normalized_payload else None,
        generated_traces=generated_traces if request.include_generated_traces else [],
        traces_used_count=len(traces_for_judge),
        ground_truth_report=ground_truth_report,
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
