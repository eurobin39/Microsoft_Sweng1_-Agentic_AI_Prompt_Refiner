"""
FastAPI Application Entry Point
TODO: Configure FastAPI app, add middleware, and include routers
"""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def _load_env() -> None:
    """
    Load .env robustly regardless of launch cwd.
    Prefer repo-root .env, then backend/.env, then dotenv discovery fallback.
    """
    repo_root_env = Path(__file__).resolve().parents[2] / ".env"
    backend_env = Path(__file__).resolve().parents[1] / ".env"

    if repo_root_env.exists():
        load_dotenv(repo_root_env, override=False)
        return
    if backend_env.exists():
        load_dotenv(backend_env, override=False)
        return

    try:
        discovered = find_dotenv(usecwd=True)
    except Exception:
        discovered = ""
    if discovered:
        load_dotenv(discovered, override=False)


_load_env()


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
