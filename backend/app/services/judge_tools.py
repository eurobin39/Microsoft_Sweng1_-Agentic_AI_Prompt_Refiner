import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def save_evaluation_result(agent_name: str, score: float, summary: str) -> bool:
    logs_dir = Path("evaluation_logs")

    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S_%f")

    safe_agent = "".join(c for c in agent_name if c.isalnum() or c in ("-", "_")).strip()
    if not safe_agent:
        safe_agent = "judge"

    filepath = logs_dir / f"{safe_agent}_{timestamp_str}.json"

    data = {
        "agent_name": agent_name,
        "timestamp_utc": now_utc.isoformat(),
        "agent_score": score,
        "summary": summary,
    }

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logger.exception("Failed to write evaluation log to %s", filepath)
        return False