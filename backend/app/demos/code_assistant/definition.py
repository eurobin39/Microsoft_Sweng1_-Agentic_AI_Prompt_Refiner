from agent_framework import tool
from agent_framework_utils import run_workflow_sync
from .agents import explain_code, refactor_code, document_code
from .workflows.graph import build_graph_workflow

_graph_workflow = None


@tool
def explain_code_tool(code: str) -> str:
    """Explain what the provided code does."""
    return explain_code(code, stream=False)


@tool
def refactor_code_tool(code: str) -> str:
    """Refactor code to be cleaner and easier to read."""
    return refactor_code(code, stream=False)


@tool
def document_code_tool(code: str) -> str:
    """Add docstrings and comments to code."""
    return document_code(code, stream=False)


def _get_graph_workflow():
    global _graph_workflow
    if _graph_workflow is None:
        _graph_workflow = build_graph_workflow()
    return _graph_workflow


def _messages_to_text(messages) -> str:
    if not messages:
        return ""
    if isinstance(messages, str):
        return messages
    parts = []
    for msg in messages:
        text = getattr(msg, "text", None) or getattr(msg, "content", None)
        parts.append(text if text is not None else str(msg))
    return "\n\n".join(parts)


def orchestrator(user_request: str, code: str, stream: bool = False) -> str:
    payload = {
        "user_request": user_request,
        "code": code,
    }
    outputs = run_workflow_sync(_get_graph_workflow(), payload)
    response = _messages_to_text(outputs)
    if stream:
        print(response)
    return response
