from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _make_json_safe(x: Any) -> Any:
    """Best-effort convert to JSON-serializable types."""
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (list, tuple)):
        return [_make_json_safe(i) for i in x]
    if isinstance(x, dict):
        return {str(k): _make_json_safe(v) for k, v in x.items()}

    # Pydantic v2
    if hasattr(x, "model_dump"):
        try:
            return _make_json_safe(x.model_dump())
        except Exception:
            pass

    # Pydantic v1
    if hasattr(x, "dict"):
        try:
            return _make_json_safe(x.dict())
        except Exception:
            pass

    # Dataclass
    if hasattr(x, "__dataclass_fields__"):
        try:
            from dataclasses import asdict

            return _make_json_safe(asdict(x))
        except Exception:
            pass

    # Fallback: stringify
    return str(x)


def save_refinement_result(
    agent_name: str,
    refined_prompt: str,
    summary: str,
    *,
    original_prompt: Optional[str] = None,
    changes: Optional[Any] = None,
    expected_impact: Optional[str] = None,
    evaluation_score_ref: Optional[Any] = None,
    full_result: Optional[Any] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist refinement output to disk as a JSON audit log.

    Writes under refinement_logs/ with unique filename:
      <agent_name>_<UTC timestamp>.json

    Returns:
      str(filepath)
    """
    logs_dir = Path("refinement_logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S_%f")

    safe_agent = "".join(c for c in agent_name if c.isalnum() or c in ("-", "_")).strip()
    if not safe_agent:
        safe_agent = "refiner"

    filepath = logs_dir / f"{safe_agent}_{timestamp_str}.json"

    payload: Dict[str, Any] = {
        "agent_name": agent_name,
        "timestamp_utc": now_utc.isoformat(),
        "refined_prompt": refined_prompt,
        "summary": summary,
    }

    # Optional expansions (allowed by issue)
    if original_prompt is not None:
        payload["original_prompt"] = original_prompt
    if changes is not None:
        payload["changes"] = _make_json_safe(changes)
    if expected_impact is not None:
        payload["expected_impact"] = expected_impact
    if evaluation_score_ref is not None:
        payload["evaluation_score_ref"] = _make_json_safe(evaluation_score_ref)
    if full_result is not None:
        payload["full_result"] = _make_json_safe(full_result)
    if extra:
        payload["extra"] = _make_json_safe(extra)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)

    return str(filepath)
