from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from app.services.refiner_tools import save_refinement_result


# ── Tools ──
# Thin wrapper: expose tool to LLM; real logic lives in services/refiner_tools.py
@tool(
    name="store_refinement_result",
    description="Persist the refinement result to disk as an audit log.",
)
def store_refinement_result(agent_name: str, refined_prompt: str, summary: str) -> str:
    return save_refinement_result(agent_name, refined_prompt, summary)


# ── Agent Definitions ──

JUDGE_SYSTEM_PROMPT = ""  # TODO:


def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO:
    raise NotImplementedError


REFINER_SYSTEM_PROMPT = ""  # TODO: Refiner team


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: Refiner team
    raise NotImplementedError