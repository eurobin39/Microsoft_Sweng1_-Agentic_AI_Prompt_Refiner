from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from backend.app.services.refiner_tools import store_refinement_result as store_refinement_result_service

# ── Tools ──
# TODO: add @tool wrappers here, importing implementations from services/judge_tools.py and refiner_tools.py

@tool
def store_refinement_result(result: dict) -> dict:
    return store_refinement_result_service(result)

# ── Agent Definitions ──

JUDGE_SYSTEM_PROMPT = ""  # TODO: 

def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: 
    raise NotImplementedError

REFINER_SYSTEM_PROMPT = ""  # TODO: Refiner team

def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: Refiner team
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[store_refinement_result],
    )