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

@tool
def store_refinement_result(result: dict) -> dict:
    return store_refinement_result_service(result)

# ── Agent Definitions ──

JUDGE_SYSTEM_PROMPT = ""  # TODO:


def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO:
    raise NotImplementedError

REFINER_SYSTEM_PROMPT = # TODO: Refiner team
    REFINER_SYSTEM_PROMPT = 
        """ 
        You are a Refiner Agent responsible for improving a system prompt ("blueprint")
        based on structured feedback from a Judge Agent.

        Your task is to analyse the Judge’s EvaluationResult and produce a refined,
        fully usable version of the original blueprint.

        Behavioural Expectations:

        - Directly address issues identified in the judge’s EvaluationResult
        - Produce actionable refinements (not vague suggestions)
        - Output a fully usable refined blueprint
        - Avoid changing parts of the blueprint that were already functioning correctly
        - Maintain clarity and internal consistency in the improved prompt

        Output Requirements:

        Return a valid JSON object matching the RefinementResult schema with the following fields:

        - refined_prompt (string)
        - changes (list of objects containing: issue_reference, change_description, reasoning)
        - expected_impact (string)
        - summary (string)

        Respond with JSON only. Do not include additional commentary.
        """


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    # TODO: Refiner team
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[store_refinement_result],
    )