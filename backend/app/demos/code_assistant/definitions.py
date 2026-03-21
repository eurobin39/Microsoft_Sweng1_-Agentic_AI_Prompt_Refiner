"""
Agent definitions for the code assistant.

Tools use Python's ast module to analyse code structure — real data the agents
can use to reason before generating their response.

Agents:
  - code_triage:     reads the request and hands off to the right specialist
  - code_explainer:  explains what code does using extract_functions + analyze_code_metrics
  - code_refactor:   rewrites code for clarity using extract_functions + analyze_code_metrics
  - code_documenter: adds docstrings/comments using check_docstrings + extract_functions
"""

import ast

from agent_framework import ChatAgent, tool
from agent_framework.azure import AzureOpenAIChatClient


# ═══════════════════════════ Tools ═══════════════════════════

@tool(name="extract_functions", description="Extract function and class signatures from the code.")
def extract_functions(code: str) -> str:
    try:
        tree = ast.parse(code)
        items = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                items.append(f"def {node.name}({', '.join(args)})")
            elif isinstance(node, ast.ClassDef):
                items.append(f"class {node.name}")
        return "\n".join(items) if items else "No functions or classes found."
    except SyntaxError as e:
        return f"Syntax error in code: {e}"


@tool(name="analyze_code_metrics", description="Analyse code metrics: line count, function count, loops, and conditionals.")
def analyze_code_metrics(code: str) -> str:
    lines = [l for l in code.splitlines() if l.strip()]
    try:
        tree = ast.parse(code)
        funcs = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        ifs = sum(1 for n in ast.walk(tree) if isinstance(n, ast.If))
        loops = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While)))
        return (
            f"Lines: {len(lines)}, Functions: {funcs}, Classes: {classes}, "
            f"If statements: {ifs}, Loops: {loops}"
        )
    except SyntaxError:
        return f"Lines: {len(lines)} (could not parse AST — check for syntax errors)"


@tool(name="check_docstrings", description="Identify which functions and classes are missing docstrings.")
def check_docstrings(code: str) -> str:
    try:
        tree = ast.parse(code)
        missing, has_docs = [], []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                ):
                    has_docs.append(node.name)
                else:
                    missing.append(node.name)
        parts = []
        if missing:
            parts.append(f"Missing docstrings: {', '.join(missing)}")
        if has_docs:
            parts.append(f"Already documented: {', '.join(has_docs)}")
        return "\n".join(parts) if parts else "No functions or classes found."
    except SyntaxError as e:
        return f"Syntax error in code: {e}"


# ═══════════════════════════ Agent Factories ═══════════════════════════

def create_triage_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_triage",
        instructions=(
            "You are a code assistant coordinator. Read the user's request and the code they provide, "
            "then hand off to the right specialist:\n"
            "- code_explainer: if they want to understand what the code does\n"
            "- code_refactor: if they want cleaner, more readable, or more efficient code\n"
            "- code_documenter: if they want docstrings or comments added\n"
            "For requests that need both refactoring and documentation, hand off to code_refactor first — "
            "it will chain to code_documenter when done."
        ),
        chat_client=chat_client,
    )


def create_explainer_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_explainer",
        instructions=(
            "Explain what the provided code does in plain English. "
            "Call extract_functions to identify the structure, and analyze_code_metrics to understand complexity. "
            "Give a clear explanation covering what each function does, its inputs and outputs, "
            "and any notable patterns or logic worth calling out."
        ),
        chat_client=chat_client,
        tools=[extract_functions, analyze_code_metrics],
    )


def create_refactor_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_refactor",
        instructions=(
            "Refactor the provided code to be cleaner and easier to read. "
            "Call extract_functions to understand the current structure and analyze_code_metrics to spot complexity issues. "
            "Add type hints, use idiomatic Python patterns, and briefly explain each change you made. "
            "If the user also wants documentation added, hand off to code_documenter after you are done."
        ),
        chat_client=chat_client,
        tools=[extract_functions, analyze_code_metrics],
    )


def create_documenter_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_documenter",
        instructions=(
            "Add docstrings and inline comments to the provided code. "
            "Call check_docstrings to identify what is missing, and extract_functions to understand the structure. "
            "Write Google-style docstrings with Args, Returns, and Examples sections where applicable."
        ),
        chat_client=chat_client,
        tools=[check_docstrings, extract_functions],
    )
