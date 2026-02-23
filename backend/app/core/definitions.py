from typing import Any

from agent_framework import ChatAgent, tool
from agent_framework.azure import AzureOpenAIChatClient

from app.services.judge_tools import save_evaluation_result
from app.services.refiner_tools import save_refinement_result


@tool(
    name="store_evaluation_result",
    description="Persist judge evaluation output to disk as an audit log.",
)
def store_evaluation_result(agent_name: str, score: float, summary: str) -> str:
    return save_evaluation_result(agent_name, score, summary)


@tool(
    name="store_refinement_result",
    description="Persist refiner output to disk as an audit log.",
)
def store_refinement_result(
    refined_prompt: str,
    summary: str,
    changes: list[dict[str, Any]] | None = None,
    expected_impact: str | None = None,
    agent_name: str = "refiner_agent",
) -> str:
    return save_refinement_result(
        agent_name=agent_name,
        refined_prompt=refined_prompt,
        summary=summary,
        changes=changes,
        expected_impact=expected_impact,
    )


JUDGE_SYSTEM_PROMPT = """
You are a Judge Agent.

Evaluate the provided blueprint and traces, then return a JSON object:
{
  "score": <float between 0 and 1>,
  "issues": ["..."],
  "strengths": ["..."],
  "summary": "..."
}

Guidelines:
- Be strict and concrete.
- Prefer actionable feedback over generic comments.
- Return JSON only.
"""


REFINER_SYSTEM_PROMPT = """
You are a Refiner Agent responsible for improving a system prompt (blueprint)
based on structured feedback from a Judge Agent.

Your task is to analyze the Judge evaluation and produce a refined,
fully usable version of the original blueprint.

Behavioral expectations:
- Directly address issues identified in the judge output.
- Produce actionable refinements.
- Output a fully usable refined blueprint.
- Avoid changing parts that already work well.
- Maintain clarity and internal consistency.

Return a valid JSON object with fields:
- refined_prompt (string)
- changes (list of objects containing: issue_reference, change_description, reasoning)
- expected_impact (string)
- summary (string)

After generating the JSON, call the tool `store_refinement_result` with:
- agent_name = "refiner_agent"
- refined_prompt = JSON.refined_prompt
- summary = JSON.summary
- changes = JSON.changes
- expected_impact = JSON.expected_impact

Respond with JSON only.
"""


def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="judge_agent",
        instructions=JUDGE_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[store_evaluation_result],
    )


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[store_refinement_result],
    )
