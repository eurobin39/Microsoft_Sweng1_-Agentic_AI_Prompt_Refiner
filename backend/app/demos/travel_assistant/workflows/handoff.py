"""
Handoff Workflow — triage-based routing between specialist agents.

Uses HandoffBuilder from agent_framework.
The triage agent receives all user input first and routes to the appropriate
specialist via automatically registered handoff tools. Specialists can also
hand off to each other (e.g. weather → packing).

Architecture:
    User → TriageAgent
              ├── handoff_to_weather_agent  → WeatherAgent
              │                                  ├── handoff_to_packing_agent → PackingAgent
              │                                  └── handoff_to_activities_agent → ActivitiesAgent
              ├── handoff_to_packing_agent  → PackingAgent
              ├── handoff_to_activities_agent → ActivitiesAgent
              └── handoff_to_booking_agent  → BookingAgent
"""

from agent_framework import HandoffBuilder
from agent_framework.azure import AzureOpenAIChatClient

from ..agents import (
    create_triage_agent,
    create_weather_agent,
    create_packing_agent,
    create_activities_agent,
    create_booking_agent,
)


def build_handoff_workflow(chat_client: AzureOpenAIChatClient):
    """
    Build a handoff workflow where triage routes to specialists.

    Specialists can hand off between each other for multi-topic requests.
    Conversation history is preserved across all handoffs.
    """
    triage = create_triage_agent(chat_client)
    weather = create_weather_agent(chat_client)
    packing = create_packing_agent(chat_client)
    activities = create_activities_agent(chat_client)
    booking = create_booking_agent(chat_client)

    workflow = (
        HandoffBuilder(
            name="travel_assistant_handoff",
            participants=[triage, weather, packing, activities, booking],
        )
        .with_start_agent(triage)
        # Configure directed handoffs: who can route to whom
        .add_handoff(triage, [weather, packing, activities, booking])
        .add_handoff(weather, [packing, activities])  # weather can chain to packing or activities
        .add_handoff(activities, [booking])            # activities can suggest bookings
        .add_handoff(booking, [weather])               # booking can check weather for travel dates
        # Terminate after a reasonable exchange
        .with_termination_condition(
            lambda conversation: len(conversation) >= 10
        )
        .build()
    )

    return workflow