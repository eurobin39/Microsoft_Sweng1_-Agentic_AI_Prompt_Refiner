"""
FastAPI Application Entry Point
TODO: Configure FastAPI app, add middleware, and include routers
"""

from fastapi import FastAPI

app = FastAPI(
    title="Agentic AI Prompt Refiner",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {"message": "Agentic AI Prompt Refiner API"}
