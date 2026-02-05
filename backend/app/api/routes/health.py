"""
Health check endpoints
TODO: Implement health check endpoint
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}