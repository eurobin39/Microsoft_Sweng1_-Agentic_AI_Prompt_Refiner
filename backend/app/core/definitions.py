import json
import difflib
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

@tool(
    name="extract_agent_prompts",
    description="Parse the trace and return a name -> instructions mapping per agent."
)
def extract_agent_prompts(trace_json: str) -> str:
    try:
        trace = json.loads(trace_json)
        prompts = {
            step.get("agent_name", "unknown"): step.get("instructions", "")
            for step in trace.get("steps", [])
        }
        return json.dumps(prompts, indent=2)
    except Exception as e:
        return f"Error extracting prompts: {str(e)}"


# TODO: implement compare_tool_usage(trace_json: str, expected_behavior: str, tools_available: str) -> str
#       Parse tools_available into a set of known tool names.
#       Extract every tool_name from trace["steps"][*]["tool_calls"][*] into a called set.
#       Infer which tools *should* have been called from expected_behavior (keyword/heuristic match
#       against the available set is fine — the judge LLM handles final reasoning).
#       Return a JSON object with three keys: "available", "called", "unexpected" (called − available),
#       and "missing" (expected − called). These sets are what the judge needs — do not ask the LLM
#       to do set arithmetic that Python can do deterministically.

# TODO: implement compare_execution_order(trace_json: str, expected_behavior: str) -> str
#       Extract the ordered list of agent_name values from trace["steps"].
#       Parse expected_behavior for agent names that appear in the trace (case-insensitive match).
#       Produce a side-by-side comparison: expected sequence vs actual sequence.
#       Flag (label clearly in the output) any agents that are missing from the actual run or appear
#       out of position relative to the expected sequence. The structural flags are the value here —
#       the judge LLM interprets severity, but the detection must happen in this function.

# TODO: implement compare_output_to_expected(final_output: str, expected_output: str, expected_behavior: str) -> str
#       Use difflib.unified_diff (or ndiff) to produce a line-by-line structural diff between
#       expected_output and final_output. Include the raw diff lines in the return value.
#       Also include a word-level similarity ratio via difflib.SequenceMatcher so the judge has a
#       numeric signal alongside the diff. Semantic assessment is still the judge LLM's job, but the
#       structural diff must be computed here — that is why difflib was imported.

# TODO: implement validate_handoffs(trace_json: str, expected_behavior: str) -> str
#       Build the list of actual (from, to) handoff pairs by iterating consecutive steps in
#       trace["steps"]. Parse expected_behavior for agent names and infer the expected handoff chain
#       from their order of mention. Compare actual vs expected handoff pairs and clearly label
#       each pair as EXPECTED, UNEXPECTED, or MISSING. Return all three categories in the JSON so
#       the judge does not have to re-derive them.


# ═══════════════════════════ Refiner Tools ═══════════════════════════

# TODO: implement diff_prompts(original: str, refined: str) -> str
#       Use difflib.unified_diff to produce a structured, line-by-line diff between original and
#       refined. Return the diff as a string (not a raw list) with a brief header showing total
#       lines added and removed. Called twice by the refiner: once on the original against itself
#       to understand structure, and once on original vs final refined to summarise all changes.

# TODO: implement estimate_token_count(prompt: str) -> str
#       Return a token estimate for the prompt. Prefer tiktoken (cl100k_base encoding) if available;
#       fall back to len(prompt) // 4 if not. Return a JSON object with "estimated_tokens",
#       "method" ("tiktoken" or "char_heuristic"), and "150pct_cap" (estimated_tokens * 1.5) so the
#       refiner can immediately see the hard limit it must not exceed.

# TODO: implement validate_prompt_structure(prompt: str) -> str
#       Check that the prompt contains all four required sections: instructions, constraints,
#       output format, and examples. Do case-insensitive keyword matching — a section counts as
#       present if its header keyword appears in the text. Return a JSON object with "present" (list
#       of found sections), "missing" (list of absent sections), and "valid" (bool: missing is empty).
#       If "valid" is false the refiner must revise before finalising.


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
        tools=[
            store_evaluation_result,
            extract_agent_prompts,
            # TODO: add compare_tool_usage, compare_execution_order,
            #       compare_output_to_expected, validate_handoffs once implemented
        ],
    )


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[
            store_refinement_result,
            # TODO: add diff_prompts, estimate_token_count, validate_prompt_structure once implemented
        ],
    )
