from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient


# ── Tools ──
# TODO: add @tool wrappers here, importing implementations from services/judge_tools.py and refiner_tools.py


# ── Agent Definitions ──

JUDGE_SYSTEM_PROMPT = ""  # TODO: 

def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: 
    raise NotImplementedError


REFINER_SYSTEM_PROMPT = ""  # TODO: Refiner team

def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: Refiner team
    raise NotImplementedError
