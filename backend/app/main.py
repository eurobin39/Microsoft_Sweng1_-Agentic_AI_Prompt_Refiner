"""
FastAPI Application Entry Point
TODO: Configure FastAPI app, add middleware, and include routers
"""

from fastapi import FastAPI
from app.api.routes import health, evaluation

from app.api.routes import resume_demo

app = FastAPI(
    title="Agentic AI Prompt Refiner",
    version="0.1.0"
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(resume_demo.router, prefix="/api/v1", tags=["Resume Demo"])

@app.get("/")
async def root():
    return {"message": "Agentic AI Prompt Refiner API"}
