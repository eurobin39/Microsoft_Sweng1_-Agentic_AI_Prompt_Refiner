import json
import os

from agent_framework import (
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
)
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from app.models.models import AgentBlueprint, EvaluationResponse, EvaluationResult, RefinementResult
from app.models.trace_logs import TraceLog
from .workflow import build_refinement_workflow

load_dotenv()


def get_chat_client() -> AzureOpenAIChatClient:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

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
