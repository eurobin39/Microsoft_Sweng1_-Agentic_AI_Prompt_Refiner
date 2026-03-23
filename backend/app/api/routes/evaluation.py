import json
from typing import AsyncGenerator, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.models import (
    AgentRefinementResult,
    BatchRefineRequest,
    EvaluationRequest,
    EvaluationResponse,
)
from app.core.runner import get_chat_client, run_evaluation, run_evaluation_stream

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
    Evaluate an AI agent's performance against its blueprint and refine its system prompt if needed.

    Use this tool when a developer wants to evaluate their agent. To call it correctly:

    1. Read the agent's blueprint JSON file and pass its contents as `blueprint`.
    2. Read all trace log JSON files (from the traces directory) and pass them as the `traces` array.
    3. Pass `blueprint` and `traces` at the root level — do NOT wrap them in an "EvaluationRequest" key.

    Schema rules to follow exactly:
    - `agents` inside each trace must be a JSON object (dict), never a string.
    - `evaluation_criteria` must be an object with keys: goals (list), constraints (list), priority_description (str).
    - `tool.parameters`, `model_parameters`, `output_schema` must be JSON objects, never strings.
    - `provider` must be one of: azure_openai, openai, anthropic, mistral, grok — omit if unknown.
    - `context` in test_cases must be a JSON object or omitted — never an empty string.
    - `duration_ms` must be an integer, not a string.
    - `handoff.reason` and `handoff.timestamp` are optional — omit if not present in the source data.

    Returns an EvaluationResult (overall_score 0–1, per-test results, summary) and optionally a
    RefinementResult with an improved system prompt when overall_score < 0.7.
    """
    try:
        return await run_evaluation(request.blueprint, request.traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
