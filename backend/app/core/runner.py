import json
import os
from pathlib import Path

from agent_framework import (
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
)
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.exceptions import ServiceInitializationError
from azure.identity import AzureCliCredential
from dotenv import find_dotenv, load_dotenv

from app.models.models import AgentBlueprint, EvaluationResponse, EvaluationResult, RefinementResult
from app.models.trace_logs import TraceLog
from .workflow import build_refinement_workflow


def _load_env_if_needed() -> None:
    # Avoid repeated filesystem work once any key is present.
    if os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_CHAT_ENDPOINT"):
        return

    repo_root_env = Path(__file__).resolve().parents[2] / ".env"
    backend_env = Path(__file__).resolve().parents[1] / ".env"

    if repo_root_env.exists():
        load_dotenv(repo_root_env, override=False)
        return
    if backend_env.exists():
        load_dotenv(backend_env, override=False)
        return

    try:
        discovered = find_dotenv(usecwd=True)
    except Exception:
        discovered = ""
    if discovered:
        load_dotenv(discovered, override=False)


def get_chat_client() -> AzureOpenAIChatClient:
    _load_env_if_needed()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "") or os.getenv("AZURE_OPENAI_CHAT_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "") or os.getenv("AZURE_OPENAI_CHAT_API_KEY", "")
    deployment = (
        os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "")
    )

    try:
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
    except ServiceInitializationError as exc:
        raise RuntimeError(
            "Azure OpenAI client initialization failed. Set required env vars: "
            "AZURE_OPENAI_ENDPOINT and one of "
            "{AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}. "
            "Also set AZURE_OPENAI_API_KEY (or use Azure CLI login)."
        ) from exc


def _extract_json(text: str) -> dict:
    """Extract a JSON object from agent output, stripping any markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in agent output: {text[:200]!r}")
    return json.loads(text[start : end + 1])


async def run_evaluation_stream(
    agent_name: str,
    blueprint: AgentBlueprint,
    traces: list[TraceLog],
    chat_client: AzureOpenAIChatClient,
):
    """Async generator yielding SSE-formatted strings with live agent output chunks."""
    workflow = build_refinement_workflow(chat_client)

    payload = {
        "blueprint": blueprint.model_dump(mode="json"),
        "traces": [t.model_dump(mode="json") for t in traces],
        "iteration": 1,
    }
    message = json.dumps(payload)

    _buffers: dict[str, list[str]] = {}
    _current_agent: str | None = None
    _last_judge_text: str = ""
    _last_refiner_text: str = ""

    async for event in workflow.run_stream(message):
        if isinstance(event, ExecutorInvokedEvent):
            _current_agent = event.executor_id
            if _current_agent:
                _buffers[_current_agent] = []
                yield f"data: {json.dumps({'type': 'agent_start', 'agent_name': agent_name, 'executor': _current_agent})}\n\n"

        elif isinstance(event, AgentRunUpdateEvent):
            executor_id = event.executor_id or _current_agent
            data = event.data
            if isinstance(data, AgentResponseUpdate):
                text = getattr(data, "text", "") or ""
                if text and executor_id:
                    _buffers.setdefault(executor_id, []).append(text)
                    yield f"data: {json.dumps({'type': 'chunk', 'agent_name': agent_name, 'executor': executor_id, 'text': text})}\n\n"

        elif isinstance(event, ExecutorCompletedEvent):
            executor_id = event.executor_id
            if executor_id and executor_id in _buffers:
                text = "".join(_buffers.pop(executor_id))
                if text.strip():
                    if executor_id == "judge_agent":
                        _last_judge_text = text
                    elif executor_id == "refiner_agent":
                        _last_refiner_text = text

    if not _last_judge_text:
        yield f"data: {json.dumps({'type': 'error', 'detail': f'No output from judge_agent for {agent_name}'})}\n\n"
        return

    evaluation = EvaluationResult(**_extract_json(_last_judge_text))
    refinement: RefinementResult | None = None
    if _last_refiner_text:
        refinement = RefinementResult(**_extract_json(_last_refiner_text))

    result_data = {
        "type": "result",
        "agent_name": agent_name,
        "evaluation": evaluation.model_dump(mode="json"),
        "refinement": refinement.model_dump(mode="json") if refinement else None,
    }
    yield f"data: {json.dumps(result_data)}\n\n"


async def run_evaluation(blueprint: AgentBlueprint, traces: list[TraceLog]) -> EvaluationResponse:
    chat_client = get_chat_client()
    workflow = build_refinement_workflow(chat_client)

    payload = {
        "blueprint": blueprint.model_dump(mode="json"),
        "traces": [t.model_dump(mode="json") for t in traces],
        "iteration": 1,
    }
    message = json.dumps(payload)

    # Per-agent streaming text buffers; reset on each ExecutorInvokedEvent
    _buffers: dict[str, list[str]] = {}
    _current_agent: str | None = None
    _last_judge_text: str = ""
    _last_refiner_text: str = ""

    async for event in workflow.run_stream(message):
        if isinstance(event, ExecutorInvokedEvent):
            _current_agent = event.executor_id
            if _current_agent:
                _buffers[_current_agent] = []

        elif isinstance(event, AgentRunUpdateEvent):
            executor_id = event.executor_id or _current_agent
            data = event.data
            if isinstance(data, AgentResponseUpdate):
                text = getattr(data, "text", "") or ""
                if text and executor_id:
                    _buffers.setdefault(executor_id, []).append(text)

        elif isinstance(event, ExecutorCompletedEvent):
            executor_id = event.executor_id
            if executor_id and executor_id in _buffers:
                text = "".join(_buffers.pop(executor_id))
                if text.strip():
                    if executor_id == "judge_agent":
                        _last_judge_text = text
                    elif executor_id == "refiner_agent":
                        _last_refiner_text = text

    if not _last_judge_text:
        raise RuntimeError("Workflow completed without any output from judge_agent")

    evaluation = EvaluationResult(**_extract_json(_last_judge_text))

    refinement: RefinementResult | None = None
    if _last_refiner_text:
        refinement = RefinementResult(**_extract_json(_last_refiner_text))

    return EvaluationResponse(evaluation=evaluation, refinement=refinement)
