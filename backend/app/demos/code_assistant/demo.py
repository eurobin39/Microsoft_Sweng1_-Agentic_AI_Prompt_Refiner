import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from code_assistant.runner import run_workflow


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

LOG_FILE = "code_assistant/log/code_assistant.log"
TRACE_DIR = "code_assistant/log/traces"


def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo():
    header("CODE ASSISTANT DEMO — GRAPH WORKFLOW")
    print("Sample code:")
    print("-" * 80)
    print(SAMPLE_CODE)
    print("-" * 80)
    print(f"Traces will be saved to: {TRACE_DIR}/\n")

    # Test 1: Explain
    header("TEST 1: Explain — 'What does this code do?'")
    run_workflow(
        user_request="What does this code do?",
        code=SAMPLE_CODE,
        mode="EXPLAIN",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    # Test 2: Refactor
    header("TEST 2: Refactor — 'Refactor this code to improve readability and add type hints'")
    run_workflow(
        user_request="Refactor this code to improve readability and add type hints",
        code=SAMPLE_CODE,
        mode="REFACTOR",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    # Test 3: Document
    header("TEST 3: Document — 'Add numpy-style docstrings to this code'")
    run_workflow(
        user_request="Add numpy-style docstrings to this code",
        code=SAMPLE_CODE,
        mode="DOCUMENT",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    # Test 4: Refactor + Document
    header("TEST 4: Refactor + Document — 'Refactor this code and then add documentation'")
    run_workflow(
        user_request="Refactor this code and then add documentation",
        code=SAMPLE_CODE,
        mode="REFACTOR_DOCUMENT",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    # Test 5: Explain (natural language variation)
    header("TEST 5: Explain — 'Can you help me understand what's going on here?'")
    run_workflow(
        user_request="Can you help me understand what's going on here?",
        code=SAMPLE_CODE,
        mode="EXPLAIN",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    # Test 6: Refactor (performance focus)
    header("TEST 6: Refactor — 'Make this code more efficient'")
    run_workflow(
        user_request="Make this code more efficient",
        code=SAMPLE_CODE,
        mode="REFACTOR",
        log_file=LOG_FILE,
        trace_dir=TRACE_DIR,
    )

    header("DEMO COMPLETE")
    print(f"Traces saved to: {TRACE_DIR}/\n")


if __name__ == "__main__":
    run_demo()
