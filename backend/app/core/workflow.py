from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient

from .definitions import create_judge_agent, create_refiner_agent


def build_refinement_workflow(chat_client: AzureOpenAIChatClient):

    judge = create_judge_agent(chat_client)
    refiner = create_refiner_agent(chat_client)

    workflow = (
        WorkflowBuilder(start_executor=judge)
        .add_edge(judge, refiner)
        .build()
    )

    return workflow