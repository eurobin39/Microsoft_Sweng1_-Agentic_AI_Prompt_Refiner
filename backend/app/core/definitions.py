from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient


# ── Tools ──
# TODO: add @tool wrappers here, importing implementations from services/judge_tools.py and refiner_tools.py


# DUMMY TOOL: Added temporarily so the file doesn't crash until Daniel pushes his code.
@tool
def store_evaluation_result(evaluation_data: dict) -> str:
    """Stores the result of the agent evaluation."""
    return "Stored"



# ── Agent Definitions ──

JUDGE_SYSTEM_PROMPT = """You are an impartial AI QA Judge. You are evaluating an AI agent's execution trace against a blueprint.

### CONTEXT PROVIDED TO YOU
1. Blueprint: Contains the agent's instructions, its test cases, and what good behaviour looks like.
2. Trace: Contains what the agent actually did, which tools it called, and what it responded.

### YOUR INSTRUCTIONS
1. Review the trace against the test cases provided in the blueprint.
2. You MUST call the `store_evaluation_result` tool to save your findings before responding.
3. Your final output MUST respond ONLY with valid JSON in the EvaluationResult structure below. Do not include markdown fences (like ```json) or any conversational text.

{
    "overall_score": <float 0.0 to 1.0>,
    "test_results": [
        {
            "test_case_description": "<string description>",
            "score": <float 0.0 to 1.0>,
            "passed": <boolean>,
            "reasoning": "<string explanation>",
            "issues": ["<string issue>", "<string issue>"]
        }
    ],
    "summary": "<string high-level diagnosis>"
}
"""
def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="judge_agent",
        instructions=JUDGE_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[store_evaluation_result],  # Written by Daniel (using dummy above for now)
    )





REFINER_SYSTEM_PROMPT = ""  # TODO: Refiner team

def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: Refiner team
    raise NotImplementedError
