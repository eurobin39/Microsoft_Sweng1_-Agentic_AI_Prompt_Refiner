"""
Code Assistant — async runner using the handoff workflow.

Streams workflow events into WorkflowTracer for structured tracing.
"""

import asyncio
import logging
import os
from typing import Any

from azure.identity import AzureCliCredential
from agent_framework import WorkflowOutputEvent
from agent_framework.azure import AzureOpenAIChatClient

from .logger import WorkflowTracer, setup_logging
from .workflow import build_handoff_workflow


def _get_chat_client() -> AzureOpenAIChatClient:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    if api_key:
        return AzureOpenAIChatClient(api_key=api_key, endpoint=endpoint, deployment_name=deployment)
    return AzureOpenAIChatClient(credential=AzureCliCredential(), endpoint=endpoint, deployment_name=deployment)


async def run_workflow(
    user_request: str,
    code: str,
    log_file: str | None = None,
    trace_dir: str = "code_assistant/log/traces",
) -> dict[str, Any]:
    setup_logging(level=logging.INFO, log_file=log_file)

    chat_client = _get_chat_client()
    workflow = build_handoff_workflow(chat_client)
    tracer = WorkflowTracer(user_input=user_request, mode="handoff")

    message = f"{user_request}\n\nCode:\n{code}"
    final_output = ""

    async for event in workflow.run_stream(message):
        tracer.capture(event)
        if isinstance(event, WorkflowOutputEvent):
            final_output = getattr(event, "text", "") or str(event)

    tracer.set_final_output(final_output)
    tracer.save(trace_dir)
    tracer.print_summary()

    return tracer.get_trace()


def run_sync(
    user_request: str,
    code: str,
    log_file: str | None = None,
    trace_dir: str = "code_assistant/log/traces",
) -> dict[str, Any]:
    return asyncio.run(run_workflow(user_request, code, log_file=log_file, trace_dir=trace_dir))
