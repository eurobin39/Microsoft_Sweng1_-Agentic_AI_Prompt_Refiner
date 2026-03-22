import json
import difflib


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
        # This actually extracts all the the instructions used by each agent in the trace
        prompts = {step.get("agent_name", "unknown"): step.get("instructions", "") for step in trace.get("steps", [])}
        return json.dumps(prompts, indent=2)
    except Exception as e:
        return f"Error extracting prompts: {str(e)}"

@tool(
    name="compare_tool_usage",
    description="Surface gaps/unexpected calls between available, expected, and actually-called tools."
)
def compare_tool_usage(trace_json: str, expected_behavior: str, tools_available: str) -> str:
    try:
        trace = json.loads(trace_json)
        called_tools = [call.get("tool_name") for step in trace.get("steps", []) for call in step.get("tool_calls", [])]
        
        return json.dumps({
            "tools_available": tools_available,
            "tools_called": called_tools,
            "expected_behavior": expected_behavior,
            "analysis": "Please evaluate if the called tools match the expected behavior."
        }, indent=2)
    except Exception as e:
        return f"Error comparing tool usage: {str(e)}"

@tool(
    name="compare_execution_order",
    description="Flag missing or out-of-order agents vs. the expected sequence."
)
def compare_execution_order(trace_json: str, expected_behavior: str) -> str:
    try:
        trace = json.loads(trace_json)
        actual_order = [step.get("agent_name") for step in trace.get("steps", [])]
        
        return json.dumps({
            "actual_execution_order": actual_order,
            "expected_behavior": expected_behavior,
            "analysis": "Please check if the actual sequence of agents aligns with the expected behavior."
        }, indent=2)
    except Exception as e:
        return f"Error comparing execution order: {str(e)}"

@tool(
    name="compare_output_to_expected",
    description="Diff final output against ground-truth; semantic assessment left to the LLM."
)
def compare_output_to_expected(final_output: str, expected_output: str, expected_behavior: str) -> str:
    return json.dumps({
        "final_output": final_output,
        "expected_output": expected_output,
        "expected_behavior": expected_behavior,
        "note": "Assess the semantic gap between final_output and expected_output."
    }, indent=2)

@tool(
    name="validate_handoffs",
    description="Verify agents handed off to each other as expected."
)
def validate_handoffs(trace_json: str, expected_behavior: str) -> str:
    try:
        trace = json.loads(trace_json)
        handoffs = []
        steps = trace.get("steps", [])
        for i in range(len(steps) - 1):
            handoffs.append({
                "from": steps[i].get("agent_name"),
                "to": steps[i+1].get("agent_name")
            })
            
        return json.dumps({
            "actual_handoffs": handoffs,
            "expected_behavior": expected_behavior
        }, indent=2)
    except Exception as e:
        return f"Error validating handoffs: {str(e)}"
#       to each other as the expected_behavior implies....


# ═══════════════════════════ Refiner Tools ═══════════════════════════

def create_judge_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="judge_agent",
        instructions=JUDGE_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[
            store_evaluation_result,
            extract_agent_prompts,
            compare_tool_usage,
            compare_execution_order,
            compare_output_to_expected,
            validate_handoffs
        ], 
    )

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
