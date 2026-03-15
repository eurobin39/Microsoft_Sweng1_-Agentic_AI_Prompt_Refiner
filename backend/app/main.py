"""
FastAPI Application Entry Point
TODO: Configure FastAPI app, add middleware, and include routers
"""

from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI
from app.api.routes import health, evaluation


app = FastAPI(
    title="Agentic AI Prompt Refiner",
    version="0.1.0"
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["Evaluation"])


@app.get("/")
async def root():
    return {"message": "Agentic AI Prompt Refiner API"}
