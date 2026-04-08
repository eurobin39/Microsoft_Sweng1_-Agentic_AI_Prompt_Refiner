import json
import difflib
from typing import Any

from agent_framework import ChatAgent, tool
from agent_framework.azure import AzureOpenAIChatClient

from app.models.models import EvaluationResult, RefinementResult
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


@tool(
    name="compare_tool_usage",
    description="Surface gaps/unexpected calls between available, expected, and actually-called tools."
)
def compare_tool_usage(trace_json: str, expected_behavior: str, tools_available: str) -> str:
    try:
        trace = json.loads(trace_json)
        
        # 1. Parse available tools into a set
        try:
            available_set = set(json.loads(tools_available))
        except (json.JSONDecodeError, ValueError):
            available_set = set([t.strip() for t in tools_available.split(',') if t.strip()])
            
        # 2. Extract actually called tools
        called_set = set()
        for step in trace.get("steps", []):
            for call in step.get("tool_calls", []):
                if tool_name := call.get("tool_name"):
                    called_set.add(tool_name)
                    
        # 3. Infer expectef tools (heuristic match)
        expected_behavior_lower = expected_behavior.lower()
        expected_set = {t for t in available_set if t.lower() in expected_behavior_lower}
        
        # 4. Set arithmetic (Unexpected = Called \ Available, Missing = Expected \ Called)
        unexpected = list(called_set - available_set)
        missing = list(expected_set - called_set)
        
        return json.dumps({
            "available": list(available_set),
            "called": list(called_set),
            "unexpected": unexpected,
            "missing": missing
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
        actual_order = [step.get("agent_name", "unknown") for step in trace.get("steps", [])]
        unique_actual = list(dict.fromkeys(actual_order))
        
        # Infer expected order by finding where known agents appear in the expected_behavior text
        expected_behavior_lower = expected_behavior.lower()
        agent_positions = []
        for agent in unique_actual:
            pos = expected_behavior_lower.find(agent.lower())
            if pos != -1:
                agent_positions.append((pos, agent))
        
        agent_positions.sort()
        expected_order = [agent for pos, agent in agent_positions]
        
        flags = []
        for i, agent in enumerate(actual_order):
            if agent not in expected_order:
                flags.append({"position": i, "agent": agent, "status": "UNEXPECTED"})
            else:
                expected_idx = expected_order.index(agent)
                actual_idx_in_unique = unique_actual.index(agent)
                if expected_idx != actual_idx_in_unique:
                    flags.append({"position": i, "agent": agent, "status": "OUT_OF_ORDER"})
                    
        for agent in expected_order:
            if agent not in actual_order:
                flags.append({"agent": agent, "status": "MISSING"})

        return json.dumps({
            "expected_sequence": expected_order,
            "actual_sequence": actual_order,
            "flags": flags
        }, indent=2)
    except Exception as e:
        return f"Error comparing execution order: {str(e)}"


@tool(
    name="compare_output_to_expected",
    description="Diff final output against ground-truth; semantic assessment left to the LLM."
)
def compare_output_to_expected(final_output: str, expected_output: str, expected_behavior: str) -> str:
    try:
        diff_lines = list(difflib.unified_diff(
            expected_output.splitlines(),
            final_output.splitlines(),
            lineterm=''
        ))
        similarity = difflib.SequenceMatcher(None, expected_output, final_output).ratio()

        return json.dumps({
            "structural_diff": "\n".join(diff_lines),
            "similarity_ratio": similarity,
            "expected_behavior": expected_behavior
        }, indent=2)
    except Exception as e:
        return f"Error comparing outputs: {str(e)}"


@tool(
    name="validate_handoffs",
    description="Verify agents handed off to each other as expected."
)
def validate_handoffs(trace_json: str, expected_behavior: str) -> str:
    try:
        trace = json.loads(trace_json)
        steps = trace.get("steps", [])
        
        actual_pairs = []
        for i in range(len(steps) - 1):
            actual_pairs.append((steps[i].get("agent_name"), steps[i+1].get("agent_name")))
            
        # Infer expected pairs using the same string-matching heuristic
        unique_actual = list(dict.fromkeys([s.get("agent_name") for s in steps]))
        expected_behavior_lower = expected_behavior.lower()
        
        agent_positions = []
        for agent in unique_actual:
            pos = expected_behavior_lower.find(agent.lower())
            if pos != -1:
                agent_positions.append((pos, agent))
        agent_positions.sort()
        expected_order = [agent for pos, agent in agent_positions]
        
        expected_pairs = []
        for i in range(len(expected_order) - 1):
            expected_pairs.append((expected_order[i], expected_order[i+1]))
            
        expected_pairs_set = set(expected_pairs)
        actual_pairs_set = set(actual_pairs)

        expected = [{"from": p[0], "to": p[1]} for p in actual_pairs if p in expected_pairs_set]
        unexpected = [{"from": p[0], "to": p[1]} for p in actual_pairs if p not in expected_pairs_set]
        missing = [{"from": p[0], "to": p[1]} for p in expected_pairs if p not in actual_pairs_set]

        return json.dumps({
            "expected": expected,
            "unexpected": unexpected,
            "missing": missing
        }, indent=2)
    except Exception as e:
        return f"Error validating handoffs: {str(e)}"


# ═══════════════════════════ Refiner Tools ═══════════════════════════

@tool(
    name="diff_prompts",
    description="Produces a structured diff between original and refined system prompt."
)
def diff_prompts(original: str, refined: str) -> str:
    diff_lines = list(difflib.unified_diff(
        original.splitlines(), 
        refined.splitlines(), 
        lineterm=''
    ))
    
    added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
    
    header = f"Lines added: {added}, Lines removed: {removed}\n\n"
    return header + "\n".join(diff_lines)


@tool(
    name="estimate_token_count",
    description="Character-based approximation or tiktoken; used to enforce the 150% size cap."
)
def estimate_token_count(prompt: str) -> str:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = len(enc.encode(prompt))
        method = "tiktoken"
    except ImportError:
        tokens = len(prompt) // 4
        method = "char_heuristic"
        
    return json.dumps({
        "estimated_tokens": tokens,
        "method": method,
        "150pct_cap": int(tokens * 1.5)
    }, indent=2)


@tool(
    name="validate_prompt_structure",
    description="Check the refined prompt still contains required sections."
)
def validate_prompt_structure(prompt: str) -> str:
    required_sections = ["instructions", "constraints", "output format", "examples"]
    prompt_lower = prompt.lower()
    
    present = [req for req in required_sections if req in prompt_lower]
    missing = [req for req in required_sections if req not in prompt_lower]
    
    return json.dumps({
        "present": present,
        "missing": missing,
        "valid": len(missing) == 0
    }, indent=2)


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
8. You MUST include every field in the schema: overall_score, test_results, and summary.
9. For each test case, include exactly one test_results item with test_case_description, score, passed, reasoning, and issues.
10. If evidence is incomplete, choose conservative values instead of omitting fields. Never leave overall_score out.

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
            compare_tool_usage,
            compare_execution_order,
            compare_output_to_expected,
            validate_handoffs
        ],
    )


def create_refiner_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="refiner_agent",
        instructions=REFINER_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[
            store_refinement_result,
            diff_prompts,
            estimate_token_count,
            validate_prompt_structure
        ],
    )