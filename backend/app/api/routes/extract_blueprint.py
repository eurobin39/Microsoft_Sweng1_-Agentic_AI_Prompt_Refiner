from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.models import AgentBlueprint, AgentBlueprintWithTraces
from app.services.blueprint_extractor import (
    extract_blueprint,
    extract_all_blueprints,
    extract_traces_from_files,
)
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


@router.post("/extract-blueprints", response_model=List[AgentBlueprintWithTraces])
async def extract_all_blueprints_from_repo(request: ExtractBlueprintRequest) -> List[AgentBlueprintWithTraces]:
    try:
        file_contents = await crawl_repo(request.github_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub crawl failed: {exc}") from exc

    try:
        blueprint_dicts = await extract_all_blueprints(file_contents)
        blueprints = [AgentBlueprint(**b) for b in blueprint_dicts]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Blueprint extraction failed: {exc}") from exc

    all_traces = extract_traces_from_files(file_contents)

    result: List[AgentBlueprintWithTraces] = []
    for bp in blueprints:
        agent_name = bp.agent.name or ""
        agent_traces = [t for t in all_traces if agent_name in t.agents]
        result.append(AgentBlueprintWithTraces(blueprint=bp, traces=agent_traces))
    return result
