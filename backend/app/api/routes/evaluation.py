"""
Evaluation endpoints
TODO: Implement evaluation endpoints for prompt evaluation and refinement
"""

from fastapi import APIRouter
from app.models.models import EvaluationRequest
router = APIRouter()


@router.post("/evaluate")
async def evaluate(request: EvaluationRequest): 
    blueprint = request.blueprint
    log = request.traces
    return  {"status": "received", "test_case_count": len(blueprint.test_cases)}
  