from __future__ import annotations

from typing import Any

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from agent_framework_utils import create_agent
from ..agents import explain_code, refactor_code, document_code


def _mode_is(*modes: str):
    def _cond(message: Any) -> bool:
        return isinstance(message, dict) and message.get("mode") in modes

    return _cond


def _ensure_payload(message: Any) -> dict:
    if isinstance(message, dict):
        return dict(message)
    return {"user_request": str(message), "code": "", "mode": "EXPLAIN"}


@executor(id="route_request")
async def route_request(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    selector = create_agent(
        name="code_assistant_router",
        instructions=(
            "Decide which operation to perform on code.\n"
            "Return ONLY one of: EXPLAIN, REFACTOR, DOCUMENT, REFACTOR_DOCUMENT."
        ),
    )
    prompt = (
        "Choose operation for this request. Return ONLY EXPLAIN, REFACTOR, DOCUMENT, or REFACTOR_DOCUMENT.\n\n"
        f"User request:\n{payload.get('user_request', '')}\n"
    )
    mode = (await selector.run(prompt)).text.strip().upper()
    if mode not in ("EXPLAIN", "REFACTOR", "DOCUMENT", "REFACTOR_DOCUMENT"):
        mode = "EXPLAIN"
    payload["mode"] = mode
    await ctx.send_message(payload)


@executor(id="explain_code")
async def explain_code_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["explanation"] = explain_code(payload.get("code", ""))
    await ctx.send_message(payload)


@executor(id="refactor_code")
async def refactor_code_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["refactored_code"] = refactor_code(payload.get("code", ""))
    await ctx.send_message(payload)


@executor(id="document_code")
async def document_code_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    source = payload.get("refactored_code") or payload.get("code", "")
    payload["documented_code"] = document_code(source)
    await ctx.send_message(payload)


@executor(id="emit_output")
async def emit_output_node(message: dict, ctx: WorkflowContext[None, str]) -> None:
    payload = _ensure_payload(message)
    mode = payload.get("mode", "EXPLAIN")
    sections: list[str] = []

    if mode == "EXPLAIN":
        sections.append(f"## Explanation\n{payload.get('explanation', '')}")
    elif mode == "REFACTOR":
        sections.append(f"## Refactored Code\n{payload.get('refactored_code', '')}")
    elif mode == "DOCUMENT":
        sections.append(f"## Documented Code\n{payload.get('documented_code', '')}")
    elif mode == "REFACTOR_DOCUMENT":
        sections.append(f"## Refactored Code\n{payload.get('refactored_code', '')}")
        sections.append(f"## Documented Code\n{payload.get('documented_code', '')}")

    await ctx.yield_output("\n\n".join(sections))


def build_graph_workflow():
    router = route_request
    explainer = explain_code_node
    refactorer = refactor_code_node
    documenter = document_code_node
    output = emit_output_node

    builder = WorkflowBuilder(start_executor=router)

    builder.add_edge(router, explainer, condition=_mode_is("EXPLAIN"))
    builder.add_edge(router, refactorer, condition=_mode_is("REFACTOR", "REFACTOR_DOCUMENT"))
    builder.add_edge(router, documenter, condition=_mode_is("DOCUMENT"))

    builder.add_edge(explainer, output)
    builder.add_edge(refactorer, documenter, condition=_mode_is("REFACTOR_DOCUMENT"))
    builder.add_edge(refactorer, output, condition=_mode_is("REFACTOR"))
    builder.add_edge(documenter, output)

    return builder.build()
