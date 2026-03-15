"""
Evaluation endpoints
"""

from fastapi import APIRouter
from app.models.models import EvaluationRequest, EvaluationResult
from app.core.runner import run_evaluation

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: EvaluationRequest): 
    # Calls the runner and returns the actual EvaluationResult
    return await run_evaluation(request.blueprint, request.traces)

@router.post("/evaluate/sync", response_model=EvaluationResult)
async def evaluate_sync(request: EvaluationRequest): 
    # Alias endpoint needed for the MCP server
    return await run_evaluation(request.blueprint, request.traces)