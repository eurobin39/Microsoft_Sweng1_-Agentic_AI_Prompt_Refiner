import os
import sys

# Add the parent directory to Python path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from code_assistant.orchestrator import orchestrator

def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def run_demo():
    # Sample code for testing
    sample_code = """
def calculate(x, y):
    return x + y

def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
"""

    print_section_header("CODE ASSISTANT ORCHESTRATOR DEMO")
    print("Sample code to analyze:")
    print("-" * 80)
    print(sample_code)
    print("-" * 80)

    # Test 1: Explanation request
    print_section_header("TEST 1: Code Explanation Request")
    print("User request: 'What does this code do?'\n")
    orchestrator("What does this code do?", sample_code, stream=True)

    # Test 2: Refactoring request with specific goal
    print_section_header("TEST 2: Code Refactoring Request")
    print("User request: 'Refactor this code to improve readability and add type hints'\n")
    orchestrator("Refactor this code to improve readability and add type hints", sample_code, stream=True)

    # Test 3: Documentation request with style
    print_section_header("TEST 3: Documentation Request")
    print("User request: 'Add numpy-style docstrings to this code'\n")
    orchestrator("Add numpy-style docstrings to this code", sample_code, stream=True)

    # Test 4: Multiple operations
    print_section_header("TEST 4: Multiple Operations Request")
    print("User request: 'Refactor this code and then add documentation'\n")
    orchestrator("Refactor this code and then add documentation", sample_code, stream=True)

    # Test 5: Natural language variation
    print_section_header("TEST 5: Natural Language Variation")
    print("User request: 'Can you help me understand what's going on here?'\n")
    orchestrator("Can you help me understand what's going on here?", sample_code, stream=True)

    # Test 6: Performance-focused refactoring
    print_section_header("TEST 6: Performance-Focused Refactoring")
    print("User request: 'Make this code more efficient'\n")
    orchestrator("Make this code more efficient", sample_code, stream=True)

    print_section_header("DEMO COMPLETE")
    print("All test cases executed successfully! ✨\n")


if __name__ == "__main__":
    run_demo()