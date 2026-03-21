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
        instructions="Read the request and route to the right agent.",
        chat_client=chat_client,
    )


def create_explainer_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_explainer",
        instructions="Explain what the code does.",
        chat_client=chat_client,
        tools=[extract_functions, analyze_code_metrics],
    )


def create_refactor_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_refactor",
        instructions="Improve the code. Hand off to code_documenter if documentation is needed.",
        chat_client=chat_client,
        tools=[extract_functions, analyze_code_metrics],
    )


def create_documenter_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="code_documenter",
        instructions="Add comments and docstrings to the code.",
        chat_client=chat_client,
        tools=[check_docstrings, extract_functions],
    )
