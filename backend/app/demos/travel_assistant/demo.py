# Demo - Interactive demo to showcase the travel assistant workflow

import os
import sys

# Add the parent directory to Python path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from travel_assistant.orchestrator import orchestrator


def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo():
    print_section_header("TRAVEL ASSISTANT ORCHESTRATOR DEMO")

    # Test 1: Weather-only request
    print_section_header("TEST 1: Weather-Only Request")
    print("User request: 'What's the weather like in Tokyo on 2026-02-15?'\n")
    result = orchestrator("What's the weather like in Tokyo on 2026-02-15?", True)
    print(f"\nResult: {result}")

    # Test 2: Packing-only request
    print_section_header("TEST 2: Packing-Only Request")
    print("User request: 'What should I pack for a trip to Iceland on 2026-03-01?'\n")
    result = orchestrator("What should I pack for a trip to Iceland on 2026-03-01?")
    print(f"\nResult: {result}")

    # Test 3: Full trip advice (both agents + composition)
    print_section_header("TEST 3: Full Trip Advice Request")
    print("User request: 'I'm travelling to Galway, Ireland on 2026-02-16. What's the weather and what should I pack?'\n")
    result = orchestrator("I'm travelling to Galway, Ireland on 2026-02-16. What's the weather and what should I pack?")
    print(f"\nResult: {result}")

    # Test 4: Natural language variation
    print_section_header("TEST 4: Natural Language Variation")
    print("User request: 'Help me prepare for my trip to Barcelona on 2026-04-10'\n")
    result = orchestrator("Help me prepare for my trip to Barcelona on 2026-04-10", True)
    print(f"\nResult: {result}")

    print_section_header("DEMO COMPLETE")


if __name__ == "__main__":
    run_demo()
