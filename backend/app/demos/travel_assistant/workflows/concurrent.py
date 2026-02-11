"""
Concurrent Workflow — fan-out to multiple agents simultaneously.

Uses ConcurrentBuilder from agent_framework.
All agents process the same user request in parallel, and results
are aggregated into a combined response.

Use case: "Tell me everything about travelling to Tokyo" — weather,
activities, and booking agents all work at the same time.

Architecture:
    User Request
        ├── WeatherAgent   ──┐
        ├── ActivitiesAgent ──┼── Aggregator → Combined Output
        └── BookingAgent   ──┘
"""

from typing import Any

from agent_framework import ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient

from ..agents import (
    create_weather_agent,
    create_activities_agent,
    create_booking_agent,
)


def _summarize_results(results: list[Any]) -> str:
    """
    Custom aggregator callback for the concurrent workflow.

    Receives a list of AgentExecutorResponse objects and combines
    the last message from each agent into a structured output.
    """
    sections = []
    for r in results:
        agent_name = r.executor_id or "Agent"
        # Get the last assistant message from the agent's response
        last_msg = r.agent_response.messages[-1].text if r.agent_response.messages else "(no response)"
        sections.append(f"━━━ {agent_name.upper()} ━━━\n{last_msg}")

    return "\n\n".join(sections)


def build_concurrent_workflow(chat_client: AzureOpenAIChatClient):
    """
    Build a concurrent workflow: weather + activities + booking in parallel.

    Uses a custom aggregator to merge all agent responses into a
    structured multi-section output.
    """
    weather = create_weather_agent(chat_client)
    activities = create_activities_agent(chat_client)
    booking = create_booking_agent(chat_client)

    workflow = (
        ConcurrentBuilder()
        .participants([weather, activities, booking])
        .with_aggregator(_summarize_results)
        .build()
    )

    return workflow