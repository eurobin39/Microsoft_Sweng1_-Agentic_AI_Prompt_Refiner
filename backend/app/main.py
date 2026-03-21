"""
FastAPI Application Entry Point
TODO: Configure FastAPI app, add middleware, and include routers
"""

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(usecwd=False))


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, evaluation, extract_blueprint


app = FastAPI(
    title="Agentic AI Prompt Refiner",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["Evaluation"])
app.include_router(extract_blueprint.router, prefix="/api/v1", tags=["Blueprint"])


@app.get("/")
async def root():
    return {"message": "Agentic AI Prompt Refiner API"}
