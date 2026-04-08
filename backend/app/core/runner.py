import json
import os
from pathlib import Path
from typing import Any

from agent_framework import (
    ChatAgent,
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
)
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.exceptions import ServiceInitializationError
from azure.identity import AzureCliCredential
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel

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


def _first_present(payload: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip():
            return float(value.strip())
    except (TypeError, ValueError):
        pass
    return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1", "pass", "passed", "success"}:
            return True
        if lowered in {"false", "no", "n", "0", "fail", "failed", "error"}:
            return False
    return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _safe_issues(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except Exception:
            return [text]
        return _safe_issues(parsed)
    if isinstance(value, dict):
        return [json.dumps(value, ensure_ascii=False)]
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        issues: list[str] = []
        for item in value:
            if item is None:
                continue
            text = _safe_str(item).strip()
            if text:
                issues.append(text)
        return issues
    text = _safe_str(value).strip()
    return [text] if text else []


def _normalize_test_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        text = _safe_str(value).strip()
        return {
            "test_case_description": text or "unknown test case",
            "score": 0.0,
            "passed": False,
            "reasoning": text or "Judge output did not include a structured test result.",
            "issues": [text] if text else ["Judge output did not include a structured test result."],
        }

    description = _safe_str(
        _first_present(
            value,
            ["test_case_description", "description", "case", "test_case", "name"],
            "unknown test case",
        ),
        "unknown test case",
    ).strip() or "unknown test case"
    score = _safe_float(_first_present(value, ["score", "overall_score", "overallScore", "value"], None), 0.0)
    passed = _safe_bool(_first_present(value, ["passed", "pass", "success"], None), default=score >= 0.5)
    reasoning = _safe_str(
        _first_present(value, ["reasoning", "analysis", "explanation", "summary", "details"], ""),
        "",
    ).strip()
    if not reasoning:
        reasoning = "Structured fallback generated from judge output."
    issues = _safe_issues(_first_present(value, ["issues", "issue", "problems", "problem", "findings"], []))
    if not issues and not passed:
        issues = [reasoning]

    return {
        "test_case_description": description,
        "score": score,
        "passed": passed,
        "reasoning": reasoning,
        "issues": issues,
    }


def _normalize_evaluation_payload(raw: Any) -> dict[str, Any]:
    candidate = raw
    if isinstance(raw, dict):
        if isinstance(raw.get("evaluation"), dict):
            candidate = raw["evaluation"]
        elif isinstance(raw.get("result"), dict):
            result_candidate = raw["result"]
            if any(
                key in result_candidate
                for key in ("overall_score", "overallScore", "test_results", "testResults", "summary")
            ):
                candidate = result_candidate

    if not isinstance(candidate, dict):
        summary = _safe_str(raw).strip() or "Judge output was not a JSON object; generated fallback evaluation."
        return {
            "overall_score": 0.0,
            "test_results": [],
            "summary": summary,
        }

    test_results_raw = _first_present(candidate, ["test_results", "testResults", "results", "tests"], [])
    normalized_test_results: list[dict[str, Any]] = []
    if isinstance(test_results_raw, dict):
        test_results_raw = list(test_results_raw.values())
    if isinstance(test_results_raw, (list, tuple)):
        normalized_test_results = [_normalize_test_result(item) for item in test_results_raw]
    elif test_results_raw not in (None, []):
        normalized_test_results = [_normalize_test_result(test_results_raw)]

    overall_score = _first_present(
        candidate,
        ["overall_score", "overallScore", "score", "average_score", "averageScore", "mean_score", "meanScore"],
        None,
    )
    if overall_score is None and normalized_test_results:
        overall_score = sum(item["score"] for item in normalized_test_results) / len(normalized_test_results)
    if overall_score is None:
        overall_score = 0.0

    summary = _first_present(candidate, ["summary", "diagnosis", "analysis", "high_level_diagnosis", "result_summary"], None)
    if summary is None:
        summary = "Judge output was incomplete; generated fallback evaluation."

    return {
        "overall_score": _safe_float(overall_score, 0.0),
        "test_results": normalized_test_results,
        "summary": _safe_str(summary, "Judge output was incomplete; generated fallback evaluation."),
    }


def _parse_evaluation_result(text: str) -> EvaluationResult:
    fallback_summary = "Judge output was incomplete; generated fallback evaluation."
    if not text.strip():
        return EvaluationResult(overall_score=0.0, test_results=[], summary=fallback_summary)

    try:
        raw_payload = _extract_json(text)
    except Exception as exc:
        return EvaluationResult(
            overall_score=0.0,
            test_results=[],
            summary=f"Judge output could not be parsed as JSON: {exc}",
        )

    normalized_payload = _normalize_evaluation_payload(raw_payload)
    try:
        return EvaluationResult(**normalized_payload)
    except Exception as exc:
        return EvaluationResult(
            overall_score=_safe_float(normalized_payload.get("overall_score"), 0.0),
            test_results=[],
            summary=_safe_str(
                normalized_payload.get("summary"),
                f"Judge output was incomplete; generated fallback evaluation: {exc}",
            ),
        )


def _normalize_refinement_payload(raw: Any) -> dict[str, Any]:
    candidate = raw
    if isinstance(raw, dict):
        if isinstance(raw.get("refinement"), dict):
            candidate = raw["refinement"]
        elif isinstance(raw.get("result"), dict):
            result_candidate = raw["result"]
            if any(
                key in result_candidate
                for key in ("refined_prompt", "refinedPrompt", "changes", "expected_impact", "expectedImpact", "summary")
            ):
                candidate = result_candidate

    if not isinstance(candidate, dict):
        text = _safe_str(raw).strip()
        return {
            "refined_prompt": text,
            "changes": [],
            "expected_impact": "Fallback generated from malformed refiner output.",
            "summary": text or "Refiner output was incomplete; generated fallback refinement.",
        }

    changes_raw = _first_present(candidate, ["changes", "modifications", "edits"], [])
    normalized_changes: list[dict[str, Any]] = []
    if isinstance(changes_raw, dict):
        changes_raw = list(changes_raw.values())
    if isinstance(changes_raw, (list, tuple)):
        for item in changes_raw:
            if isinstance(item, dict):
                normalized_changes.append(
                    {
                        "issue_reference": _safe_str(
                            _first_present(item, ["issue_reference", "issueReference", "issue", "reference"], "unknown issue"),
                            "unknown issue",
                        ).strip() or "unknown issue",
                        "change_description": _safe_str(
                            _first_present(item, ["change_description", "changeDescription", "description", "change"], "No description provided."),
                            "No description provided.",
                        ).strip() or "No description provided.",
                        "reasoning": _safe_str(
                            _first_present(item, ["reasoning", "reason", "why"], "No reasoning provided."),
                            "No reasoning provided.",
                        ).strip() or "No reasoning provided.",
                    }
                )
            elif item is not None:
                text = _safe_str(item).strip()
                if text:
                    normalized_changes.append(
                        {
                            "issue_reference": "unknown issue",
                            "change_description": text,
                            "reasoning": "Derived from malformed refiner output.",
                        }
                    )

    refined_prompt = _first_present(
        candidate,
        ["refined_prompt", "refinedPrompt", "prompt", "system_prompt", "systemPrompt"],
        None,
    )
    if refined_prompt is None:
        refined_prompt = _safe_str(raw).strip()

    expected_impact = _first_present(candidate, ["expected_impact", "expectedImpact", "impact"], None)
    if expected_impact is None:
        expected_impact = "Refined prompt should better address the judge feedback."

    summary = _first_present(candidate, ["summary", "diagnosis", "analysis", "result_summary"], None)
    if summary is None:
        summary = "Refiner output was incomplete; generated fallback refinement."

    return {
        "refined_prompt": _safe_str(refined_prompt, ""),
        "changes": normalized_changes,
        "expected_impact": _safe_str(expected_impact, "Refined prompt should better address the judge feedback."),
        "summary": _safe_str(summary, "Refiner output was incomplete; generated fallback refinement."),
    }


def _parse_refinement_result(text: str) -> RefinementResult:
    fallback_summary = "Refiner output was incomplete; generated fallback refinement."
    if not text.strip():
        return RefinementResult(
            refined_prompt="",
            changes=[],
            expected_impact="Fallback generated because the refiner produced no output.",
            summary=fallback_summary,
        )

    try:
        raw_payload = _extract_json(text)
    except Exception as exc:
        return RefinementResult(
            refined_prompt=text.strip(),
            changes=[],
            expected_impact="Fallback generated because the refiner output could not be parsed.",
            summary=f"Refiner output could not be parsed as JSON: {exc}",
        )

    normalized_payload = _normalize_refinement_payload(raw_payload)
    try:
        return RefinementResult(**normalized_payload)
    except Exception as exc:
        return RefinementResult(
            refined_prompt=_safe_str(normalized_payload.get("refined_prompt"), text.strip()),
            changes=[],
            expected_impact=_safe_str(
                normalized_payload.get("expected_impact"),
                "Fallback generated because the refiner output was incomplete.",
            ),
            summary=_safe_str(
                normalized_payload.get("summary"),
                f"Refiner output was incomplete; generated fallback refinement: {exc}",
            ),
        )


def _extract_structured_candidate(text: str, nested_keys: list[str]) -> dict[str, Any] | None:
    try:
        raw_payload = _extract_json(text)
    except Exception:
        return None

    if not isinstance(raw_payload, dict):
        return None

    for key in nested_keys:
        nested_value = raw_payload.get(key)
        if isinstance(nested_value, dict):
            return nested_value
    return raw_payload


async def _repair_structured_output(
    chat_client: AzureOpenAIChatClient,
    *,
    label: str,
    model_cls: type[BaseModel],
    raw_text: str,
    failure_reason: str,
) -> BaseModel | None:
    repair_agent = ChatAgent(
        chat_client=chat_client,
        name=f"{label}_repair_agent",
        instructions=(
            f"You repair malformed {label} output. Return only valid JSON matching {model_cls.__name__}. "
            "Do not include markdown fences or commentary."
        ),
    )
    repair_prompt = f"""Repair the following invalid {label} output into a valid {model_cls.__name__} JSON object.

Validation error:
{failure_reason}

Raw output:
{raw_text}

Return only the corrected JSON object.
"""

    try:
        response = await repair_agent.run(
            repair_prompt,
            options={"response_format": model_cls, "temperature": 0.0},
        )
    except Exception:
        return None

    try:
        repaired_value = response.value
        if repaired_value is not None:
            return repaired_value
    except Exception:
        pass

    try:
        if response.text.strip():
            return model_cls.model_validate_json(response.text)
    except Exception:
        pass

    return None


async def _parse_or_repair_evaluation_result(
    chat_client: AzureOpenAIChatClient,
    text: str,
) -> EvaluationResult:
    candidate = _extract_structured_candidate(text, ["evaluation", "result"])
    if candidate is not None:
        try:
            return EvaluationResult.model_validate(candidate)
        except Exception as exc:
            repaired = await _repair_structured_output(
                chat_client,
                label="judge",
                model_cls=EvaluationResult,
                raw_text=text,
                failure_reason=str(exc),
            )
            if isinstance(repaired, EvaluationResult):
                return repaired
    else:
        repaired = await _repair_structured_output(
            chat_client,
            label="judge",
            model_cls=EvaluationResult,
            raw_text=text,
            failure_reason="Judge output was not a valid JSON object.",
        )
        if isinstance(repaired, EvaluationResult):
            return repaired

    return _parse_evaluation_result(text)


async def _parse_or_repair_refinement_result(
    chat_client: AzureOpenAIChatClient,
    text: str,
) -> RefinementResult:
    candidate = _extract_structured_candidate(text, ["refinement", "result"])
    if candidate is not None:
        try:
            return RefinementResult.model_validate(candidate)
        except Exception as exc:
            repaired = await _repair_structured_output(
                chat_client,
                label="refiner",
                model_cls=RefinementResult,
                raw_text=text,
                failure_reason=str(exc),
            )
            if isinstance(repaired, RefinementResult):
                return repaired
    else:
        repaired = await _repair_structured_output(
            chat_client,
            label="refiner",
            model_cls=RefinementResult,
            raw_text=text,
            failure_reason="Refiner output was not a valid JSON object.",
        )
        if isinstance(repaired, RefinementResult):
            return repaired

    return _parse_refinement_result(text)


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
        evaluation = EvaluationResult(
            overall_score=0.0,
            test_results=[],
            summary=f"Judge agent produced no output for {agent_name}; generated fallback evaluation.",
        )
    else:
        evaluation = await _parse_or_repair_evaluation_result(chat_client, _last_judge_text)
    refinement: RefinementResult | None = None
    if _last_refiner_text:
            refinement = await _parse_or_repair_refinement_result(chat_client, _last_refiner_text)

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
        evaluation = EvaluationResult(
            overall_score=0.0,
            test_results=[],
            summary="Workflow completed without any output from judge_agent; generated fallback evaluation.",
        )
    else:
        evaluation = await _parse_or_repair_evaluation_result(chat_client, _last_judge_text)

    refinement: RefinementResult | None = None
    if _last_refiner_text:
            refinement = await _parse_or_repair_refinement_result(chat_client, _last_refiner_text)

    return EvaluationResponse(evaluation=evaluation, refinement=refinement)
