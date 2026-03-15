from fastapi import APIRouter, HTTPException

from app.models.models import EvaluationRequest, EvaluationResponse
from app.core.runner import run_evaluation

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    try:
        return await run_evaluation(request.blueprint, request.traces)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
