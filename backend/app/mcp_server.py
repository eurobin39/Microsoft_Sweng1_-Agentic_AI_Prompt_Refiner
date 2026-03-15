from __future__ import annotations

from typing import Any, TypedDict


class _EvidencePayloadSchema(TypedDict):
    """Required evidence fields used by the MCP payload.."""

    logs: Any | None
    ground_truth_content: Any | None


class PayloadInputSchema(_EvidencePayloadSchema, total=False):
    """Schema used by MCP tools for payload ingestion."""

    workspace: str
    agent_description: str
    system_prompt: str
    definition_py_content: str
    prompt_sources: Any
    files: Any
    tools: Any
    user_input: str
    copilot_user_input: str
    require_user_input: bool | str | int
    ground_truth: str
    log_sources: Any
    logs_files: Any
    context_files: list[str]
    case_id: str
    metadata: dict[str, Any]
    context: dict[str, Any]
    max_iters: int | str | float


def _normalize_payload_shape(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Fill missing optional fields so the MCP payload shape stays stable."""
    normalized = dict(payload)
    shape_status: dict[str, str] = {}

    defaults: dict[str, Any] = {
        "logs": None,
        "ground_truth_content": None,
        "log_sources": [],
        "tools": [],
        "metadata": {},
    }

    for key, default_value in defaults.items():
        if key in normalized and normalized[key] is not None:
            shape_status[key] = "provided"
            continue

        if isinstance(default_value, list):
            normalized[key] = []
        elif isinstance(default_value, dict):
            normalized[key] = {}
        else:
            normalized[key] = default_value

        if key in payload:
            shape_status[key] = "normalized_from_null"
        else:
            shape_status[key] = "auto_filled"

    return normalized, shape_status


def _as_bool(value: Any, default: bool = True) -> bool:
    """Coerce loosely typed payload values into a boolean flag."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _as_int(value: Any, default: int | None = None) -> int | None:
    """Coerce payload values into an optional integer."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return int(text)
        except ValueError:
            return default
    return default


def _to_payload_case(payload: PayloadInputSchema | dict[str, Any] | None):
    """Normalize incoming tool payload before deeper case construction."""
    if payload is None:
        payload = {}

    if not isinstance(payload, dict):
        raise ValueError("payload_input must be a JSON object.")

    # Some clients wrap the actual payload as {"payload_input": {...}}
    nested_payload = payload.get("payload_input")
    if isinstance(nested_payload, dict):
        payload = nested_payload

    payload, payload_shape = _normalize_payload_shape(payload)

    metadata_raw = payload.get("metadata")
    if metadata_raw is not None and not isinstance(metadata_raw, dict):
        raise ValueError("metadata must be an object.")
    metadata: dict[str, Any] = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
    metadata["payload_shape"] = payload_shape

    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        raise ValueError("context must be an object when provided.")
    context_obj: dict[str, Any] | None = context if isinstance(context, dict) else None

    user_input = payload.get("user_input")
    if not isinstance(user_input, str) or not user_input.strip():
        alt_user_input = payload.get("copilot_user_input")
        if isinstance(alt_user_input, str):
            user_input = alt_user_input
        elif context_obj is not None and isinstance(context_obj.get("user_input"), str):
            user_input = context_obj.get("user_input")
        else:
            if _as_bool(payload.get("require_user_input"), True):
                raise ValueError("Missing required field: user_input")
            user_input = ""

    return payload, payload_shape, metadata, context_obj, user_input