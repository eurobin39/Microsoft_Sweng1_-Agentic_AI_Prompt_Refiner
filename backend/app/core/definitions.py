from typing import Any

from agent_framework import ChatAgent, tool
from agent_framework.azure import AzureOpenAIChatClient

from app.services.judge_tools import save_evaluation_result
from app.services.refiner_tools import save_refinement_result


@tool(
    name="store_evaluation_result",
    description="Persist judge evaluation output to disk as an audit log.",
)
def store_evaluation_result(agent_name: str, score: float, summary: str) -> bool:
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

- Focus only on the 3 most critical issues identified by the judge.
- Do not rewrite the entire prompt.
- Make minimal targeted improvements.
- Keep the refined prompt length similar to the original.
- Avoid unnecessary expansion.

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
