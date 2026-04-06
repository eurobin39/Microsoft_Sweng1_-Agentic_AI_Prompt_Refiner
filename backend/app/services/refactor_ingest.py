from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.models.models import AgentBlueprint
from app.models.trace_logs import TraceLog
from app.services.blueprint_extractor import extract_blueprint, extract_traces_from_files
from app.services.github_crawler import crawl_repo


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return value["items"]
    return []


def _coerce_repo_files(repo_files: Any) -> Dict[str, str]:
    if isinstance(repo_files, dict):
        return {str(path): str(content) for path, content in repo_files.items()}
    if isinstance(repo_files, list):
        out: Dict[str, str] = {}
        for item in repo_files:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            content = item.get("content")
            if path and content is not None:
                out[str(path)] = str(content)
        return out
    return {}


def _collect_test_cases(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    test_cases = _as_list(payload.get("test_cases"))
    if test_cases:
        normalized: List[Dict[str, Any]] = []
        for case in test_cases:
            if isinstance(case, dict) and case.get("input"):
                normalized.append(
                    {
                        "description": case.get("description"),
                        "input": str(case["input"]),
                        "expected_output": case.get("expected_output"),
                        "expected_behavior": case.get("expected_behavior"),
                        "context": case.get("context"),
                    }
                )
        if normalized:
            return normalized

    test_inputs = _as_list(payload.get("test_inputs"))
    if test_inputs:
        return [{"input": str(item), "expected_behavior": payload.get("expected_behavior")} for item in test_inputs]

    fallback_input = payload.get("sample_input") or payload.get("input") or payload.get("user_request") or "Run one basic end-to-end test."
    return [{"input": str(fallback_input), "expected_behavior": "Agent should follow its instructions and produce a valid response."}]


def _collect_tools(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_tools = _as_list(payload.get("tools"))
    tools: List[Dict[str, Any]] = []
    for idx, tool in enumerate(raw_tools):
        if isinstance(tool, str):
            tools.append({"name": tool, "description": f"Tool {tool}", "parameters": None})
            continue
        if not isinstance(tool, dict):
            continue
        name = tool.get("name") or tool.get("tool") or f"tool_{idx + 1}"
        description = tool.get("description") or f"Tool {name}"
        parameters = tool.get("parameters")
        if isinstance(parameters, str):
            try:
                parameters = json.loads(parameters)
            except Exception:
                parameters = None
        tools.append({"name": str(name), "description": str(description), "parameters": parameters})
    return tools


def _synthesise_blueprint(payload: Dict[str, Any]) -> AgentBlueprint:
    prompt = (
        payload.get("system_prompt")
        or payload.get("instructions")
        or payload.get("prompt")
        or payload.get("agent_prompt")
        or "You are a reliable AI assistant. Use available tools when needed and return a concise, accurate answer."
    )

    criteria_payload = {
        "goals": _as_list(payload.get("goals")),
        "constraints": _as_list(payload.get("constraints")),
        "priority_description": payload.get("priority_description"),
    }
    if not criteria_payload["goals"] and not criteria_payload["constraints"] and not criteria_payload["priority_description"]:
        criteria_payload = None

    candidate = {
        "agent": {
            "name": payload.get("agent_name") or "genai_agent",
            "description": payload.get("agent_description") or "Auto-generated from flexible refactor payload",
            "system_prompt": str(prompt),
            "model": payload.get("model"),
            "provider": payload.get("provider"),
            "model_parameters": _as_dict(payload.get("model_parameters")) or None,
            "tools": _collect_tools(payload),
            "output_format": payload.get("output_format"),
            "output_schema": _as_dict(payload.get("output_schema")) or None,
        },
        "test_cases": _collect_test_cases(payload),
        "evaluation_criteria": criteria_payload,
    }
    return AgentBlueprint.model_validate(candidate)


def _collect_traces_from_payload(payload: Dict[str, Any]) -> List[TraceLog]:
    candidates: List[Any] = []
    for key in ("traces", "trace_logs", "logs", "execution_traces"):
        if key in payload:
            candidates.extend(_as_list(payload.get(key)))

    parsed: List[TraceLog] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        try:
            parsed.append(TraceLog.model_validate(item))
        except Exception:
            continue
    return parsed


def _build_fallback_trace(payload: Dict[str, Any], blueprint: AgentBlueprint) -> TraceLog:
    agent_name = blueprint.agent.name or "genai_agent"
    sample_input = (
        payload.get("sample_input")
        or payload.get("input")
        or payload.get("user_request")
        or (blueprint.test_cases[0].input if blueprint.test_cases else "No input provided")
    )
    observed_output = payload.get("observed_output")
    fallback = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "sequential",
        "input": str(sample_input),
        "agents": {
            agent_name: {
                "instructions": blueprint.agent.system_prompt,
                "tools_available": [t.name for t in blueprint.agent.tools],
                "tool_calls": [],
                "output": observed_output,
            }
        },
        "execution_order": [agent_name],
        "handoffs": [],
        "final_output": observed_output,
    }
    return TraceLog.model_validate(fallback)


async def normalize_refactor_payload(payload: Dict[str, Any]) -> Tuple[AgentBlueprint, List[TraceLog], List[str]]:
    notes: List[str] = []
    normalized_payload = dict(payload)
    raw_payload = payload.get("raw_payload")
    if raw_payload is not None:
        merged = _as_dict(raw_payload)
        if merged:
            normalized_payload = {**merged, **normalized_payload}
            notes.append("Applied raw_payload JSON merge before normalization.")

    file_contents: Dict[str, str] = {}
    repo_files = _coerce_repo_files(normalized_payload.get("repo_files"))
    if repo_files:
        file_contents = repo_files
        notes.append("Using repo_files from request payload.")
    elif normalized_payload.get("github_url"):
        file_contents = await crawl_repo(str(normalized_payload["github_url"]))
        notes.append("Fetched repository files from github_url.")

    blueprint_input = normalized_payload.get("blueprint")
    blueprint: AgentBlueprint
    if blueprint_input is not None:
        try:
            blueprint = AgentBlueprint.model_validate(_as_dict(blueprint_input))
            notes.append("Using explicit blueprint from request.")
        except Exception:
            if file_contents:
                extracted = await extract_blueprint(file_contents)
                blueprint = AgentBlueprint.model_validate(extracted)
                notes.append("Explicit blueprint invalid; extracted blueprint from repository context.")
            else:
                blueprint = _synthesise_blueprint(normalized_payload)
                notes.append("Explicit blueprint invalid; synthesized blueprint from flexible request fields.")
    elif file_contents:
        extracted = await extract_blueprint(file_contents)
        blueprint = AgentBlueprint.model_validate(extracted)
        notes.append("Extracted blueprint from repository context.")
    else:
        blueprint = _synthesise_blueprint(normalized_payload)
        notes.append("Synthesized blueprint from flexible request fields.")

    traces = _collect_traces_from_payload(normalized_payload)
    if file_contents:
        traces.extend(extract_traces_from_files(file_contents))
    if traces:
        notes.append(f"Accepted {len(traces)} trace(s) after normalization.")
    else:
        traces = [_build_fallback_trace(normalized_payload, blueprint)]
        notes.append("No valid traces found; generated one fallback trace.")

    return blueprint, traces, notes
