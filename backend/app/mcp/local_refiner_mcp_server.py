from __future__ import annotations

import json
import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP


DEFAULT_BASE_URL = os.getenv("PROMPT_REFINER_BASE_URL", "http://127.0.0.1:8000")
mcp = FastMCP("prompt-refiner-local")


def _base_url() -> str:
    return os.getenv("PROMPT_REFINER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _json_load_if_needed(payload: str | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if payload is None:
        return {}
    if not isinstance(payload, str):
        return {"observed_output": str(payload)}
    text = (payload or "").strip()
    if not text:
        return {}
    if text in {'""', "''", "null", "None"}:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Gracefully accept accidental JSON strings and plain text by wrapping
        # into a safe fallback payload instead of failing the tool call.
        return {"observed_output": text} if text else {}

    if isinstance(data, dict):
        return data
    if data in (None, "", []):
        return {}
    if isinstance(data, list):
        return {"test_inputs": data}
    if isinstance(data, str):
        return {"observed_output": data} if data.strip() else {}
    return {"observed_output": str(data)}


def _post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_base_url()}{path}"
    with httpx.Client(timeout=120) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def health() -> Dict[str, Any]:
    """Check whether local Prompt Refiner API is reachable."""
    url = f"{_base_url()}/api/health"
    with httpx.Client(timeout=10) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


@mcp.tool(name="Optimize")
def optimize(payload: str) -> Dict[str, Any]:
    """
    Flexible prompt refinement.
    `payload` should be a JSON object string for POST /api/v1/Optimize.
    """
    data = _json_load_if_needed(payload)
    return _post_json("/api/v1/Optimize", data)


@mcp.tool(name="Optimize-run")
def optimize_run(payload: str) -> Dict[str, Any]:
    """
    Runtime execution + trace generation + judge/refiner.
    `payload` should be a JSON object string for POST /api/v1/Optimize-run.
    """
    data = _json_load_if_needed(payload)
    return _post_json("/api/v1/Optimize-run", data)


@mcp.tool()
def evaluate(payload: str) -> Dict[str, Any]:
    """
    Strict evaluation endpoint.
    `payload` should be a JSON object string for POST /api/v1/evaluate.
    """
    data = _json_load_if_needed(payload)
    return _post_json("/api/v1/evaluate", data)


@mcp.tool()
def extract_blueprints(github_url: str) -> Dict[str, Any]:
    """Extract one blueprint bundle per agent from a GitHub repository URL."""
    return {"items": _post_json("/api/v1/extract-blueprints", {"github_url": github_url})}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
