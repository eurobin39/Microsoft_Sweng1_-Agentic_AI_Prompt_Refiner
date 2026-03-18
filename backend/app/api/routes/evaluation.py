"""
Evaluation endpoints
TODO: Implement evaluation endpoints for prompt evaluation and refinement
"""

from fastapi import APIRouter
from app.models.models import EvaluationRequest
from app.core.runner import run_refinement_pipeline

router = APIRouter()

async def run_pipeline(request: EvaluationRequest):
    blueprint = request.blueprint
    traces = request.traces
    return await run_refinement_pipeline(blueprint, traces)

@router.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    return await run_pipeline(request)


@router.post("/evaluate/sync")
async def evaluate_sync(request: EvaluationRequest):
    return await run_pipeline(request)