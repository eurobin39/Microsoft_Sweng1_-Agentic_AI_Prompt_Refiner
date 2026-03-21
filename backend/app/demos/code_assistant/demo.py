import os
import sys

from dotenv import load_dotenv

# Allow running directly from this directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from app.demos.code_assistant.runner import run_sync


SAMPLE_CODE = """
def calculate(x, y):
    return x + y

def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
"""

TRACE_DIR = "code_assistant/log/traces"
LOG_FILE = "code_assistant/log/code_assistant.log"


def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo() -> None:
    header("CODE ASSISTANT DEMO — HANDOFF WORKFLOW")
    print("Sample code:")
    print("-" * 40)
    print(SAMPLE_CODE)
    print("-" * 40)
    print(f"Traces will be saved to: {TRACE_DIR}/\n")

    scenarios = [
        "What does this code do?",
        "Refactor this to improve readability and add type hints.",
        "Add Google-style docstrings to this code.",
        "Refactor this code and then add full documentation.",
        "Can you help me understand what's going on here?",
        "Make this code more efficient.",
    ]

    for i, request in enumerate(scenarios, 1):
        header(f"TEST {i}: {request}")
        run_sync(request, SAMPLE_CODE, log_file=LOG_FILE, trace_dir=TRACE_DIR)

    header("DEMO COMPLETE")
    print(f"Traces saved to: {TRACE_DIR}/\n")


if __name__ == "__main__":
    run_demo()
