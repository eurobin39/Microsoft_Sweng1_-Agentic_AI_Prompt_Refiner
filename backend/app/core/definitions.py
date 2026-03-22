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
    

# ═══════════════════════════ Judge Tools ═══════════════════════════

# TODO: implement extract_agent_prompts(trace_json: str) -> str
#       Parse the trace and return each agent's name → instructions mapping.
#       Lets the judge check whether agents were correctly prompted for the task.

# TODO: implement compare_tool_usage(trace_json: str, expected_behavior: str, tools_available: str) -> str
#       Compare tools available vs tools that should have been used (inferred from expected_behavior)
#       vs tools actually called (from trace tool_calls). Surface any gaps or unexpected calls.

# TODO: implement compare_execution_order(trace_json: str, expected_behavior: str) -> str
#       Extract actual execution_order from trace and compare against the expected agent sequence
#       inferred from expected_behavior. Flag missing or out-of-order agents.

# TODO: implement compare_output_to_expected(final_output: str, expected_output: str, expected_behavior: str) -> str
#       Diff the agent's final_output against the ground-truth expected_output from the test case.
#       Structural diff is heuristic; semantic gap assessment is left to the judge LLM.

# TODO: implement validate_handoffs(trace_json: str, expected_behavior: str) -> str
#       Extract actual handoffs from the trace and check whether the right agents handed off
#       to each other as the expected_behavior implies.


# ═══════════════════════════ Refiner Tools ═══════════════════════════

# TODO: implement diff_prompts(original: str, refined: str) -> str
#       Return a structured diff showing exactly what changed between the original
#       and refined system prompt.

# TODO: implement estimate_token_count(prompt: str) -> str
#       Estimate the token count of the prompt (character-based approximation or tiktoken).
#       Guards against the refined prompt ballooning in size.

# TODO: implement validate_prompt_structure(prompt: str) -> str
#       Check that the refined prompt still contains key sections
#       (instructions, constraints, output format, examples).


# ═══════════════════════════ System Prompts ═══════════════════════════

JUDGE_SYSTEM_PROMPT = """You are an impartial AI QA Judge. You are evaluating an AI agent's execution trace against a blueprint.

### CONTEXT PROVIDED TO YOU
1. Blueprint: Contains the agent's instructions, its test cases, and what good behaviour looks like.
2. Trace: Contains what the agent actually did, which tools it called, and what it responded.

### YOUR INSTRUCTIONS
1. Call extract_agent_prompts to get the instructions each agent ran with.
2. For each test case, call compare_tool_usage to check which tools were available, which should have been used, and which were actually called.
3. Call compare_execution_order to check whether agents ran in the right sequence.
4. Call compare_output_to_expected to diff the agent's final output against the expected output in each test case.
5. Call validate_handoffs to verify agents handed off to each other correctly.
6. Use the results from all tools to reason about each test case and produce your score.
7. Your final output MUST respond ONLY with valid JSON in the EvaluationResult structure below. Do not include markdown fences (like ```json) or any conversational text.

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

### CONTEXT PROVIDED TO YOU
1. Original Blueprint: The system prompt that was evaluated.
2. Judge Output: Structured evaluation with scores, issues, and a summary diagnosis.

### YOUR INSTRUCTIONS
1. Call diff_prompts on the original prompt against itself to understand its current structure before making changes.
2. For each issue identified by the judge, plan a targeted fix that addresses the root cause.
3. Call estimate_token_count on the original prompt to establish a baseline size. Your refined prompt must not exceed 150% of the original token count.
4. Call validate_prompt_structure on your drafted refined prompt to confirm it still contains all required sections (instructions, constraints, output format, examples).
5. If validate_prompt_structure flags missing sections, revise and validate again before finalising.
6. Call diff_prompts with the original and your final refined prompt to produce a structured summary of all changes.
7. Your final output MUST respond ONLY with valid JSON in the structure below. Do not include markdown fences or any conversational text.

{
    "refined_prompt": "<string — the full, usable refined system prompt>",
    "changes": [
        {
            "issue_reference": "<string — which judge issue this addresses>",
            "change_description": "<string — what was changed>",
            "reasoning": "<string — why this change fixes the issue>"
        }
    ],
    "expected_impact": "<string — how these changes should improve agent behaviour>",
    "summary": "<string — high-level description of the refinement>"
}

Behavioral expectations:
- Directly address issues identified in the judge output.
- Produce actionable refinements.
- Output a fully usable refined blueprint.
- Avoid changing parts that already work well.
- Maintain clarity and internal consistency.
"""


# ═══════════════════════════ Agent Factories ═══════════════════════════

def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="judge_agent",
        instructions=JUDGE_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[],  # TODO: add judge tools once implemented
    )


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[],  # TODO: add refiner tools once implemented
    )
