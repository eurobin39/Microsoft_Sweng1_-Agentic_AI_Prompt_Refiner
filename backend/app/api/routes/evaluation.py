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


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
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
