"""
Evaluation endpoints
TODO: Implement evaluation endpoints for prompt evaluation and refinement
"""

from fastapi import APIRouter
from app.models.models import EvaluationRequest
from app.core.runner import run_refinement_pipeline

router = APIRouter()


@router.post("/evaluate")
async def evaluate(request: EvaluationRequest):

    blueprint = request.blueprint
    traces = request.traces
    result = await run_refinement_pipeline(blueprint, traces)
    
    return result