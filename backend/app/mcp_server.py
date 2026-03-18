from __future__ import annotations

import argparse
import json
import os
from typing import Any

from typing_extensions import TypedDict

from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

from backend.app.core.definitions import create_judge_agent, create_refiner_agent
##
class MCPPayload(TypedDict, total=False):
    assistant_name: str
    workspace: str
    user_input: str
    system_prompt: str
    blueprint: Any
    trace: Any
    logs: Any | None
    ground_truth_content: Any | None
    context: dict[str, Any]
    metadata: dict[str, Any]
    case_id: str
    max_iters: int | str | float


def _coerce_int(value: Any, fallback: int = 1) -> int:
    if value is None:
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return fallback
    return fallback


def _coerce_bool(value: Any, fallback: bool = True) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return fallback


def _ensure_object(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object.")
    return dict(value)


def _ensure_request(payload_input: MCPPayload | dict[str, Any] | None) -> dict[str, Any]:
    if payload_input is None:
        raw: dict[str, Any] = {}
    elif isinstance(payload_input, dict):
        raw = dict(payload_input)
    else:
        raise ValueError("payload_input must be a JSON object.")

    nested = raw.get("payload_input")
    if isinstance(nested, dict):
        raw = dict(nested)

    metadata = _ensure_object(raw.get("metadata"), "metadata")
    context = _ensure_object(raw.get("context"), "context")

    request = {
        "assistant_name": str(raw.get("assistant_name") or context.get("project") or "unknown_assistant"),
        "workspace": raw.get("workspace") or ".",
        "user_input": raw.get("user_input") or context.get("user_input") or "",
        "system_prompt": raw.get("system_prompt") or context.get("system_prompt") or "",
        "blueprint": raw.get("blueprint"),
        "trace": raw.get("trace"),
        "logs": raw.get("logs"),
        "ground_truth_content": raw.get("ground_truth_content"),
        "context": context,
        "metadata": metadata,
        "case_id": raw.get("case_id"),
        "max_iters": _coerce_int(raw.get("max_iters"), 1),
    }

    return request


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except TypeError:
        return str(value)


def _resolve_blueprint_text(request: dict[str, Any]) -> str:
    explicit_blueprint = request.get("blueprint")
    if explicit_blueprint is not None:
        return _stringify(explicit_blueprint).strip()

    direct_prompt = request.get("system_prompt")
    if isinstance(direct_prompt, str) and direct_prompt.strip():
        return direct_prompt.strip()

    context = request.get("context") or {}
    prompts = context.get("current_system_prompts")

    if isinstance(prompts, dict) and prompts:
        blocks: list[str] = []
        for name, text in prompts.items():
            if isinstance(text, str) and text.strip():
                blocks.append(f"[{name}]\n{text.strip()}")
        return "\n\n".join(blocks)

    return ""


def _resolve_trace_text(request: dict[str, Any]) -> str:
    explicit_trace = request.get("trace")
    if explicit_trace is not None:
        return _stringify(explicit_trace)

    logs = request.get("logs")
    if logs is not None:
        return _stringify(logs)

    return ""


def _build_judge_input(request: dict[str, Any]) -> str:
    assistant_name = request.get("assistant_name", "unknown_assistant")
    user_input = request.get("user_input", "")
    blueprint = _resolve_blueprint_text(request)
    trace = _resolve_trace_text(request)
    ground_truth = _stringify(request.get("ground_truth_content"))

    return (
        f"Assistant: {assistant_name}\n\n"
        "Please evaluate the following assistant execution.\n\n"
        f"User Input:\n{user_input}\n\n"
        f"Blueprint:\n{blueprint}\n\n"
        f"Execution Trace:\n{trace}\n\n"
        f"Ground Truth:\n{ground_truth}\n"
    )


def _build_refiner_input(request: dict[str, Any], judge_output: str) -> str:
    assistant_name = request.get("assistant_name", "unknown_assistant")
    user_input = request.get("user_input", "")
    blueprint = _resolve_blueprint_text(request)
    trace = _resolve_trace_text(request)
    ground_truth = _stringify(request.get("ground_truth_content"))

    return (
        f"Assistant: {assistant_name}\n\n"
        "Please improve the following blueprint using the judge feedback.\n\n"
        f"User Input:\n{user_input}\n\n"
        f"Current Blueprint:\n{blueprint}\n\n"
        f"Execution Trace:\n{trace}\n\n"
        f"Ground Truth:\n{ground_truth}\n\n"
        f"Judge Feedback:\n{judge_output}\n"
    )


def _make_chat_client() -> AzureOpenAIChatClient:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = (
        os.getenv("AZURE_OPENAI_DEPLOYMENT")
        or os.getenv("AZURE_OPENAI_MODEL")
        or "gpt-4o-mini"
    )

    if api_key:
        return AzureOpenAIChatClient(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment,
        )

    return AzureOpenAIChatClient(
        credential=AzureCliCredential(),
        endpoint=endpoint,
        deployment_name=deployment,
    )


def _call_judge(request: dict[str, Any]) -> dict[str, Any]:
    client = _make_chat_client()
    judge_agent = create_judge_agent(client)
    judge_input = _build_judge_input(request)

    result = judge_agent.run(judge_input)
    output_text = getattr(result, "text", None) or str(result)

    return {
        "assistant_name": request.get("assistant_name"),
        "case_id": request.get("case_id"),
        "evaluation": output_text,
        "metadata": request.get("metadata", {}),
    }


def _call_refiner(request: dict[str, Any], judge_output: str) -> dict[str, Any]:
    client = _make_chat_client()
    refiner_agent = create_refiner_agent(client)
    refiner_input = _build_refiner_input(request, judge_output)

    result = refiner_agent.run(refiner_input)
    output_text = getattr(result, "text", None) or str(result)

    return {
        "assistant_name": request.get("assistant_name"),
        "case_id": request.get("case_id"),
        "refinement": output_text,
        "metadata": request.get("metadata", {}),
    }


def _run_single_refinement(request: dict[str, Any]) -> dict[str, Any]:
    evaluation_result = _call_judge(request)
    judge_output = evaluation_result["evaluation"]

    refinement_result = _call_refiner(request, judge_output)

    return {
        "assistant_name": request.get("assistant_name"),
        "case_id": request.get("case_id"),
        "evaluation": evaluation_result,
        "refinement": refinement_result,
        "metadata": request.get("metadata", {}),
    }


def _run_loop(request: dict[str, Any]) -> dict[str, Any]:
    rounds: list[dict[str, Any]] = []
    total_iters = max(1, request.get("max_iters", 1))

    working_request = dict(request)
    latest_eval = ""
    latest_refinement = ""

    for idx in range(total_iters):
        evaluation_result = _call_judge(working_request)
        latest_eval = evaluation_result["evaluation"]

        refinement_result = _call_refiner(working_request, latest_eval)
        latest_refinement = refinement_result["refinement"]

        rounds.append(
            {
                "iteration": idx + 1,
                "evaluation": latest_eval,
                "refinement": latest_refinement,
            }
        )

        working_request = dict(working_request)
        working_request["blueprint"] = latest_refinement

    return {
        "assistant_name": request.get("assistant_name"),
        "case_id": request.get("case_id"),
        "iterations": rounds,
        "final_evaluation": latest_eval,
        "final_refinement": latest_refinement,
        "metadata": request.get("metadata", {}),
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-refiner-mcp",
        description="Run the Agentic AI Prompt Refiner MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("PROMPT_REFINER_MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument(
        "--host",
        default=os.getenv("PROMPT_REFINER_MCP_HOST", "127.0.0.1"),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PROMPT_REFINER_MCP_PORT", "8000")),
    )
    parser.add_argument(
        "--mount-path",
        default=os.getenv("PROMPT_REFINER_MCP_MOUNT_PATH", "/"),
    )
    parser.add_argument(
        "--streamable-http-path",
        default=os.getenv("PROMPT_REFINER_MCP_STREAMABLE_HTTP_PATH", "/mcp"),
    )
    parser.add_argument(
        "--sse-path",
        default=os.getenv("PROMPT_REFINER_MCP_SSE_PATH", "/sse"),
    )
    parser.add_argument(
        "--message-path",
        default=os.getenv("PROMPT_REFINER_MCP_MESSAGE_PATH", "/messages/"),
    )
    parser.add_argument(
        "--stateless-http",
        default=os.getenv("PROMPT_REFINER_MCP_STATELESS_HTTP", "true"),
        choices=["true", "false", "1", "0", "yes", "no", "on", "off"],
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("PROMPT_REFINER_MCP_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_cli().parse_args(argv)

    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError(
            "MCP SDK is not installed. Install with: pip install -e .[mcp]"
        ) from exc

    mcp = FastMCP(
        "copilot-prompt-refiner",
        host=args.host,
        port=args.port,
        mount_path=args.mount_path,
        sse_path=args.sse_path,
        message_path=args.message_path,
        streamable_http_path=args.streamable_http_path,
        stateless_http=_coerce_bool(args.stateless_http, True),
        log_level=args.log_level,
    )

    @mcp.tool()
    def evaluate_prompt(payload_input: MCPPayload | None = None) -> dict[str, Any]:
        request = _ensure_request(payload_input)
        return _call_judge(request)

    @mcp.tool()
    def refine_prompt(payload_input: MCPPayload | None = None) -> dict[str, Any]:
        request = _ensure_request(payload_input)
        return _run_single_refinement(request)

    @mcp.tool()
    def run_refine_pipeline(payload_input: MCPPayload | None = None) -> dict[str, Any]:
        request = _ensure_request(payload_input)
        return _run_loop(request)

    mcp.run(
        transport=args.transport,
        mount_path=args.mount_path if args.transport == "sse" else None,
    )


if __name__ == "__main__":
    main()