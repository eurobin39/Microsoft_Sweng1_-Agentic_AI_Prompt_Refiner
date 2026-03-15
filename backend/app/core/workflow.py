from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient

from .definitions import create_judge_agent, create_refiner_agent


def build_refinement_workflow(chat_client: AzureOpenAIChatClient):
    judge = create_judge_agent(chat_client)
    refiner = create_refiner_agent(chat_client)

    return (
        WorkflowBuilder(start_executor=judge)  # type: ignore[call-arg]
        .add_edge(judge, refiner, condition=lambda msg: msg.get("overall_score", 1.0) < 0.7)
        .build()
    )
