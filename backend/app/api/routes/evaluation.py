from typing import List

from fastapi import APIRouter, HTTPException

from app.models.models import (
    AgentRefinementResult,
    BatchRefineRequest,
    EvaluationRequest,
    EvaluationResponse,
)
from app.core.runner import run_evaluation

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    try:
        return await run_evaluation(request.blueprint, request.traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
