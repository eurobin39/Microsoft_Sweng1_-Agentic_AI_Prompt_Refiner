from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.models import AgentBlueprint
from app.services.blueprint_extractor import extract_blueprint
from app.services.github_crawler import crawl_repo

router = APIRouter()


class ExtractBlueprintRequest(BaseModel):
    github_url: str


@router.post("/extract-blueprint", response_model=AgentBlueprint)
async def extract_blueprint_from_repo(request: ExtractBlueprintRequest) -> AgentBlueprint:
    try:
        file_contents = await crawl_repo(request.github_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub crawl failed: {exc}") from exc

    try:
        blueprint_dict = await extract_blueprint(file_contents)
        return AgentBlueprint(**blueprint_dict)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Blueprint extraction failed: {exc}") from exc
