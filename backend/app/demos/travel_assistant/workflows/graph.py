"""
Graph Workflow — deterministic routing via WorkflowBuilder.

Routes the user request to one or more specialist nodes based on intent:
  WEATHER     → weather_node → emit_output
  PACKING     → weather_node → packing_node → emit_output
  ACTIVITIES  → activities_node → emit_output
  BOOKING     → booking_node → emit_output
  FULL        → weather_node → packing_node → activities_node → emit_output

Each node calls tool functions directly (no agent round-trip) and formats
a plain-text section into the shared payload.
"""

from __future__ import annotations

import json
from typing import Any

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from agent_framework_utils import create_agent
from ..weather_api import live_weather, live_forecast
from ..mock_data import (
    mock_packing_list,
    mock_activities,
    mock_local_tips,
    mock_search_flights,
    mock_search_hotels,
)


def _mode_is(*modes: str):
    def _cond(message: Any) -> bool:
        return isinstance(message, dict) and message.get("mode") in modes

    return _cond


def _ensure_payload(message: Any) -> dict:
    if isinstance(message, dict):
        return dict(message)
    return {"user_request": str(message), "destination": "unknown"}


@executor(id="route_request")
async def route_request(message: Any, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    selector = create_agent(
        name="travel_router",
        instructions=(
            "Extract the destination and choose a travel workflow mode.\n"
            "Return ONLY a JSON object: {\"destination\": \"...\", \"mode\": \"...\"}\n"
            "Mode must be one of: WEATHER, PACKING, ACTIVITIES, BOOKING, FULL."
        ),
    )
    prompt = (
        "Extract destination and choose mode for this travel request.\n"
        "Return ONLY JSON: {\"destination\": \"City\", \"mode\": \"MODE\"}\n\n"
        f"Request: {payload.get('user_request', '')}"
    )
    raw = (await selector.run(prompt)).text.strip()
    try:
        result = json.loads(raw)
        payload["destination"] = result.get("destination", payload.get("destination", "unknown"))
        mode = result.get("mode", "WEATHER").upper()
    except (json.JSONDecodeError, AttributeError):
        mode = "WEATHER"
    if mode not in ("WEATHER", "PACKING", "ACTIVITIES", "BOOKING", "FULL"):
        mode = "WEATHER"
    payload["mode"] = mode
    await ctx.send_message(payload)


@executor(id="weather_node")
async def weather_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    destination = payload.get("destination", "unknown")
    current = live_weather(destination)
    forecast = live_forecast(destination, days=5)
    payload["weather_current"] = current
    payload["weather_forecast"] = forecast
    payload["weather_summary"] = current  # used by packing_node
    await ctx.send_message(payload)


@executor(id="packing_node")
async def packing_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    weather_summary = payload.get("weather_summary", "")
    packing = mock_packing_list(weather_summary, trip_type="city")
    payload["packing"] = packing
    await ctx.send_message(payload)


@executor(id="activities_node")
async def activities_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    destination = payload.get("destination", "unknown")
    activities = mock_activities(destination, category="all")
    tips = mock_local_tips(destination)
    payload["activities"] = activities
    payload["local_tips"] = tips
    await ctx.send_message(payload)


@executor(id="booking_node")
async def booking_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    destination = payload.get("destination", "unknown")
    origin = payload.get("origin", "Dublin")
    flights = mock_search_flights(origin, destination)
    hotels = mock_search_hotels(destination)
    payload["flights"] = flights
    payload["hotels"] = hotels
    await ctx.send_message(payload)


@executor(id="emit_output")
async def emit_output_node(message: dict, ctx: WorkflowContext[None, str]) -> None:
    payload = _ensure_payload(message)
    mode = payload.get("mode", "WEATHER")
    destination = payload.get("destination", "unknown")
    sections: list[str] = [f"# Travel Assistant — {destination}"]

    if payload.get("weather_current"):
        sections.append(f"## Weather\n{payload['weather_current']}")
    if payload.get("weather_forecast"):
        sections.append(f"## Forecast\n{payload['weather_forecast']}")
    if payload.get("packing"):
        sections.append(f"## Packing List\n{payload['packing']}")
    if payload.get("activities"):
        sections.append(f"## Activities\n{payload['activities']}")
    if payload.get("local_tips"):
        sections.append(f"## Local Tips\n{payload['local_tips']}")
    if payload.get("flights"):
        sections.append(f"## Flights\n{payload['flights']}")
    if payload.get("hotels"):
        sections.append(f"## Hotels\n{payload['hotels']}")

    await ctx.yield_output("\n\n".join(sections))


def build_graph_workflow():
    router = route_request
    weather = weather_node
    packing = packing_node
    activities = activities_node
    booking = booking_node
    output = emit_output_node

    builder = WorkflowBuilder(start_executor=router)

    builder.add_edge(router, weather, condition=_mode_is("WEATHER", "PACKING", "FULL"))
    builder.add_edge(router, activities, condition=_mode_is("ACTIVITIES"))
    builder.add_edge(router, booking, condition=_mode_is("BOOKING"))

    builder.add_edge(weather, packing, condition=_mode_is("PACKING", "FULL"))
    builder.add_edge(weather, output, condition=_mode_is("WEATHER"))

    builder.add_edge(packing, activities, condition=_mode_is("FULL"))
    builder.add_edge(packing, output, condition=_mode_is("PACKING"))

    builder.add_edge(activities, output)
    builder.add_edge(booking, output)

    return builder.build()
