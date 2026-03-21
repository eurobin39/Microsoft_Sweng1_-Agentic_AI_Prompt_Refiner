import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running directly from this directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from app.demos.code_assistant.runner import run_sync
from app.models.trace_logs import TraceLog


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
TRACE_DIR = str(Path(__file__).parent / "log" / "traces")
LOG_FILE = str(Path(__file__).parent / "log" / "code_assistant.log")


def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo() -> list[TraceLog]:
    header("CODE ASSISTANT DEMO — HANDOFF WORKFLOW")

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    code = ground_truth["code"]
    test_cases = ground_truth["test_cases"]

    print(f"Running {len(test_cases)} scenarios from ground truth.")
    print(f"Traces will be saved to: {TRACE_DIR}/\n")

    traces: list[TraceLog] = []
    for i, tc in enumerate(test_cases, 1):
        header(f"TEST {i}: {tc['user_request']}")
        trace_dict = run_sync(tc["user_request"], code, log_file=LOG_FILE, trace_dir=TRACE_DIR)
        traces.append(TraceLog.model_validate(trace_dict))

    header("DEMO COMPLETE")
    print(f"Saved {len(traces)} traces to: {TRACE_DIR}/\n")
    return traces


if __name__ == "__main__":
    run_demo()
