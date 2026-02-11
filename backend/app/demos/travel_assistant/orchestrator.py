"""
Travel Assistant Orchestrator (compatibility layer).

This wrapper preserves the older orchestrator import path used by CI tests.
It avoids requiring Azure/OpenAI credentials by default, and falls back to
simple, deterministic routing using local tools.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from .mock_data import mock_packing_list
from .weather_api import live_weather
from .runner import run_sync


logger = logging.getLogger("travel_assistant")

_WEATHER_KEYWORDS = (
    "weather", "forecast", "temperature", "rain", "snow", "sunny", "cloudy", "wind"
)
_PACKING_KEYWORDS = (
    "pack", "packing", "bring", "wear", "clothes", "clothing", "luggage", "suitcase"
)


def _extract_destination(text: str) -> Optional[str]:
    if not text:
        return None

    match = re.search(
        r"(?:to|in|for|around|near)\s+([A-Za-z][A-Za-z\s\-',.]*)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    candidate = match.group(1)
    candidate = re.split(r"[?.!,]", candidate, maxsplit=1)[0]
    candidate = re.sub(
        r"\b(next|tomorrow|today|this|on|at|by|with|and)\b.*$",
        "",
        candidate,
        flags=re.IGNORECASE,
    ).strip()

    return candidate or None


def _wants_weather(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in _WEATHER_KEYWORDS)


def _wants_packing(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in _PACKING_KEYWORDS)


def _format_weather_summary(weather_json: str) -> str:
    try:
        payload = json.loads(weather_json)
    except Exception:
        return weather_json

    current = payload.get("current", {})
    destination = payload.get("destination", "your destination")
    temp_c = current.get("temperature_c")
    temp_f = current.get("temperature_f")
    condition = current.get("condition", "weather")

    if temp_c is not None and temp_f is not None:
        return (
            f"Weather in {destination}: {condition}. "
            f"Temperature {temp_c}°C / {temp_f}°F."
        )
    if temp_c is not None:
        return f"Weather in {destination}: {condition}. Temperature {temp_c}°C."

    return f"Weather in {destination}: {condition}."

def _is_weak_output(text: str) -> bool:
    if not text:
        return True
    if len(text.strip()) < 12:
        return True
    lower = text.lower()
    has_weather = any(k in lower for k in _WEATHER_KEYWORDS)
    has_packing = any(k in lower for k in _PACKING_KEYWORDS)
    return not (has_weather or has_packing)

def orchestrator(user_request: str, stream: bool = False) -> str:
    """
    Route travel requests to weather/packing helpers.

    If Azure OpenAI credentials are present, this can run the full
    Microsoft Agent Framework workflow. Otherwise, it uses a lightweight
    rules-based fallback suitable for CI.
    """
    if not user_request or not user_request.strip():
        return "Please provide a destination and what you need help with."

    # Only use MAF when explicitly enabled. This keeps CI/local tests stable
    # even if Azure env vars are set on the machine.
    if os.getenv("TRAVEL_ASSISTANT_USE_MAF", "").lower() in {"1", "true", "yes"}:
        logger.info("Orchestrator path: MAF (TRAVEL_ASSISTANT_USE_MAF enabled)")
        print("[travel_assistant] orchestrator path: MAF (TRAVEL_ASSISTANT_USE_MAF enabled)")
        trace = run_sync(
            user_request=user_request,
            mode="handoff",
            stream=stream,
            log_file=None,
            trace_dir="travel_assistant/log/traces",
        )
        output = trace.get("final_output") or ""

        if not output:
            agents = trace.get("agents", {}) or {}
            pieces = []
            for agent in ("weather_agent", "packing_agent", "activities_agent", "booking_agent", "triage_agent"):
                agent_out = (agents.get(agent) or {}).get("output", "")
                if agent_out:
                    pieces.append(agent_out.strip())
            output = "\n\n".join(pieces).strip()

        if _is_weak_output(output):
            logger.warning("MAF output weak/empty; using fallback composition")
            print("[travel_assistant] MAF output weak/empty; using fallback composition")
            # Fall through to fallback path
        else:
            return output

    logger.info("Orchestrator path: fallback (rules + mock/live tools)")
    print("[travel_assistant] orchestrator path: fallback (rules + mock/live tools)")

    destination = _extract_destination(user_request)
    if not destination:
        return "Please provide a destination so I can help with weather or packing advice."

    needs_weather = _wants_weather(user_request)
    needs_packing = _wants_packing(user_request)

    # Default behavior for ambiguous queries: provide both.
    if not needs_weather and not needs_packing:
        needs_weather = True
        needs_packing = True

    outputs: list[str] = []
    weather_json = ""

    if needs_weather:
        weather_json = live_weather(destination)
        outputs.append(_format_weather_summary(weather_json))

    if needs_packing:
        summary = weather_json if weather_json else destination
        packing_json = mock_packing_list(summary, "general")
        outputs.append("Packing suggestions:\n" + packing_json)

    return "\n\n".join(outputs).strip()
