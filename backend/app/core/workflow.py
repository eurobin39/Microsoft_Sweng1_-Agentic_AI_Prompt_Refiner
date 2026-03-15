import json

from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient

from .definitions import create_judge_agent, create_refiner_agent


def _should_refine(response) -> bool:
    """Condition: route to refiner when the judge's overall_score is below threshold.

    The condition receives an AgentExecutorResponse whose .agent_response.text
    is the judge's raw JSON output.
    """
    try:
        text = response.agent_response.text
        data = json.loads(text)
        return data.get("overall_score", 1.0) < 0.7
    except Exception:
        return False  # if we can't parse, don't route to refiner


def build_refinement_workflow(chat_client: AzureOpenAIChatClient):
    judge = create_judge_agent(chat_client)
    refiner = create_refiner_agent(chat_client)

    return (
        WorkflowBuilder()
        .set_start_executor(judge)
        .add_edge(judge, refiner, condition=_should_refine)
        .build()
    )
