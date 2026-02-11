"""
Travel Assistant — main runner.

Provides a unified interface for running any of the three workflow patterns:
  - handoff: triage routes to specialist agents who can hand off to each other
  - concurrent: multiple agents work in parallel on the same request
  - sequential: agents chain in sequence (e.g. weather → packing)

All workflows produce structured JSON traces for evaluator consumption.
"""

import os
import asyncio
import logging
from typing import Any, cast

from agent_framework import (
    AgentResponseUpdate,
    ChatMessage,
    WorkflowOutputEvent,
)
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from .workflows import build_handoff_workflow, build_concurrent_workflow, build_sequential_workflow
from .logger import WorkflowTracer, setup_logging

load_dotenv()


def get_chat_client() -> AzureOpenAIChatClient:
    """
    Create an AzureOpenAIChatClient from environment variables.

    Supports API key auth (AZURE_OPENAI_API_KEY) or Azure CLI credential (az login).
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    if api_key:
        return AzureOpenAIChatClient(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment,
        )
    else:
        return AzureOpenAIChatClient(
            credential=AzureCliCredential(),
            endpoint=endpoint,
            deployment_name=deployment,
        )


async def run_workflow(
    user_request: str,
    mode: str = "handoff",
    stream: bool = True,
    log_file: str | None = None,
    trace_dir: str = "travel_assistant/log/traces",
) -> dict[str, Any]:
    """
    Run a travel assistant workflow with structured tracing.

    Args:
        user_request: The user's travel question.
        mode: Workflow pattern — "handoff", "concurrent", or "sequential".
        stream: If True, print agent responses as they stream.
        log_file: Optional path for log file.
        trace_dir: Directory to save JSON traces.

    Returns:
        The full trace dict (also saved to trace_dir as JSON).
    """
    setup_logging(level=logging.INFO, log_file=log_file)

    chat_client = get_chat_client()

    # Build the requested workflow
    if mode == "handoff":
        workflow = build_handoff_workflow(chat_client)
    elif mode == "concurrent":
        workflow = build_concurrent_workflow(chat_client)
    elif mode == "sequential":
        workflow = build_sequential_workflow(chat_client)
    else:
        raise ValueError(f"Unknown mode: {mode}. Choose 'handoff', 'concurrent', or 'sequential'.")

    # Set up tracer
    tracer = WorkflowTracer(user_input=user_request, mode=mode)

    # Run with streaming
    final_output = ""
    last_response_id: str | None = None

    async for event in workflow.run_stream(user_request):
        tracer.capture(event)

        if stream and isinstance(event, WorkflowOutputEvent):
            data = event.data
            if isinstance(data, AgentResponseUpdate):
                rid = data.response_id
                if rid != last_response_id:
                    if last_response_id is not None:
                        print()
                    author = data.author_name or "agent"
                    print(f"\n🤖 [{author}]: ", end="", flush=True)
                    last_response_id = rid
                print(data.text, end="", flush=True)

            elif isinstance(data, list):
                messages = cast(list[ChatMessage], data)
                final_output = "\n\n".join(
                    f"[{m.author_name or m.role}]: {m.text}" for m in messages if m.text
                )

            elif isinstance(data, str):
                final_output = data

    if stream:
        print("\n")

    # Finalise trace
    tracer.set_final_output(final_output)
    tracer.save(trace_dir)
    tracer.print_summary()

    logging.getLogger("travel_assistant").info(tracer.summary())

    return tracer.get_trace()


def run_sync(
    user_request: str,
    mode: str = "handoff",
    stream: bool = True,
    log_file: str | None = None,
    trace_dir: str = "traces",
) -> dict[str, Any]:
    """Synchronous wrapper."""
    return asyncio.run(run_workflow(user_request, mode, stream, log_file, trace_dir))