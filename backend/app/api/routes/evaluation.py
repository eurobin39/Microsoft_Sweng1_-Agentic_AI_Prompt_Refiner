"""
Evaluation endpoints
TODO: Implement evaluation endpoints for prompt evaluation and refinement
"""

from fastapi import APIRouter
from app.models.models import EvaluationRequest
from app.core.runner import run_evaluation #, run_refinement

router = APIRouter()


@router.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    result = await run_evaluation(
        blueprint=request.blueprint,
        traces=request.traces,
    )
    return result

#@router.post("/refine")
#async def refine(request: RefinementRequest):