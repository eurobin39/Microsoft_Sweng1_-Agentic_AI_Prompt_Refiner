"""
Handoff Workflow — triage-based routing between specialist agents.

The triage agent receives all input first and routes to the appropriate
specialist via automatically registered handoff tools. The refactor agent
can also chain to the documenter for combined requests.

Architecture:
    User → code_triage
              ├── handoff_to_code_explainer  → code_explainer
              ├── handoff_to_code_refactor   → code_refactor
              │                                  └── handoff_to_code_documenter → code_documenter
              └── handoff_to_code_documenter → code_documenter
"""

from agent_framework import HandoffBuilder
from agent_framework.azure import AzureOpenAIChatClient

from .definitions import (
    create_triage_agent,
    create_explainer_agent,
    create_refactor_agent,
    create_documenter_agent,
)


def build_handoff_workflow(chat_client: AzureOpenAIChatClient):
    triage = create_triage_agent(chat_client)
    explainer = create_explainer_agent(chat_client)
    refactor = create_refactor_agent(chat_client)
    documenter = create_documenter_agent(chat_client)

    return (
        HandoffBuilder(
            name="code_assistant_handoff",
            participants=[triage, explainer, refactor, documenter],
        )
        .with_start_agent(triage)
        .add_handoff(triage, [explainer, refactor, documenter])
        .add_handoff(refactor, [documenter])  # refactor chains to documenter for combined requests
        .with_termination_condition(lambda conversation: len(conversation) >= 10)
        .build()
    )
