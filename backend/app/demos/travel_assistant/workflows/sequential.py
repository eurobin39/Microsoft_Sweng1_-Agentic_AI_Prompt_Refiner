"""
Sequential Workflow — chained agent pipeline.

Uses SequentialBuilder from agent_framework.
Each agent processes in turn, with full conversation history passed
to the next agent in the sequence.

Use case: "What should I pack for Iceland?" — WeatherAgent gets the
weather first, then PackingAgent uses that context to generate a
tailored packing list.

Architecture:
    User Request → WeatherAgent → PackingAgent → Output
    (each agent sees the full conversation so far)
"""

from agent_framework import SequentialBuilder
from agent_framework.azure import AzureOpenAIChatClient

from ..agents import (
    create_weather_agent,
    create_packing_agent,
)


def build_sequential_workflow(chat_client: AzureOpenAIChatClient):
    """
    Build a sequential workflow: weather → packing.

    The packing agent sees the weather agent's response in the
    conversation history, so it can tailor its suggestions.
    """
    weather = create_weather_agent(chat_client)
    packing = create_packing_agent(chat_client)

    workflow = (
        SequentialBuilder()
        .participants([weather, packing])
        .build()
    )

    return workflow