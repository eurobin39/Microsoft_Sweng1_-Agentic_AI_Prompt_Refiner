"""
Handoff Workflow — triage-based routing between specialist agents.

Architecture:
    User → triage_agent
              ├── handoff_to_weather_agent   → weather_agent
              │                                  └── handoff_to_packing_agent → packing_agent
              ├── handoff_to_packing_agent   → packing_agent
              ├── handoff_to_activities_agent → activities_agent
              │                                  └── handoff_to_booking_agent → booking_agent
              └── handoff_to_booking_agent   → booking_agent
"""

from agent_framework import HandoffBuilder
from agent_framework.azure import AzureOpenAIChatClient

from .definitions import (
    create_triage_agent,
    create_weather_agent,
    create_packing_agent,
    create_activities_agent,
    create_booking_agent,
)


def build_handoff_workflow(chat_client: AzureOpenAIChatClient):
    triage = create_triage_agent(chat_client)
    weather = create_weather_agent(chat_client)
    packing = create_packing_agent(chat_client)
    activities = create_activities_agent(chat_client)
    booking = create_booking_agent(chat_client)

    return (
        HandoffBuilder(
            name="travel_assistant_handoff",
            participants=[triage, weather, packing, activities, booking],
        )
        .with_start_agent(triage)
        .add_handoff(triage, [weather, packing, activities, booking])
        .add_handoff(weather, [packing, activities])
        .add_handoff(activities, [booking])
        .with_termination_condition(lambda conversation: len(conversation) >= 10)
        .build()
    )
