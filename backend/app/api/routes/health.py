"""
Health check endpoints
TODO: Implement health check endpoint
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/ping")
async def ping():
    return {"message": "pong"}


# TODO: Add GET /health endpoint here