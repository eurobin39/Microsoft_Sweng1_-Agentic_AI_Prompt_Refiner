"""
Travel Assistant Demo — Microsoft Agent Framework

Demonstrates three workflow patterns with structured tracing:
  1. HANDOFF: Triage agent routes to specialists who hand off between each other
  2. SEQUENTIAL: Weather → Packing chain (packing needs weather context)
  3. CONCURRENT: Weather + Activities + Booking agents work in parallel

Each run produces a JSON trace in traces/ for evaluator consumption.

Prerequisites:
  pip install agent-framework --pre azure-identity python-dotenv

  Environment variables (or .env file):
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
    AZURE_OPENAI_API_KEY=your-key       (or use `az login`)
    AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
"""

import os
import sys
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from travel_assistant.runner import run_workflow


def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  🧳 {title}")
    print("=" * 80 + "\n")


async def main() -> None:
    log_file = "travel_assistant/log/travel_assistant.log"
    trace_dir = "travel_assistant/log/traces"


    header("TRAVEL ASSISTANT — MICROSOFT AGENT FRAMEWORK DEMO")
    print(f"📝 Event logs: {log_file}")
    print(f"📄 JSON traces: {trace_dir}/\n")

    # ─── 1. HANDOFF: Weather-only request ───
    header("1. HANDOFF — Weather-Only Request")
    print("User: 'What's the weather like in Tokyo?'\n")
    await run_workflow(
        "What's the weather like in Tokyo?",
        mode="handoff",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    # ─── 2. HANDOFF: Booking request ───
    header("2. HANDOFF — Booking Request")
    print("User: 'Find me flights from Dublin to Barcelona'\n")
    await run_workflow(
        "Find me flights from Dublin to Barcelona",
        mode="handoff",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    # ─── 3. HANDOFF: Multi-topic (triage → weather → packing) ───
    header("3. HANDOFF — Multi-Topic (Weather → Packing handoff)")
    print("User: 'What's the weather in Reykjavik and what should I pack for hiking?'\n")
    await run_workflow(
        "What's the weather in Reykjavik and what should I pack for hiking?",
        mode="handoff",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    # ─── 4. SEQUENTIAL: Weather → Packing pipeline ───
    header("4. SEQUENTIAL — Weather → Packing Pipeline")
    print("User: 'What should I pack for a beach trip to Bali?'\n")
    await run_workflow(
        "What should I pack for a beach trip to Bali?",
        mode="sequential",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    # ─── 5. CONCURRENT: Full trip overview (all agents in parallel) ───
    header("5. CONCURRENT — Full Trip Overview (parallel agents)")
    print("User: 'Tell me everything about travelling to Galway, Ireland'\n")
    await run_workflow(
        "Tell me everything about travelling to Galway, Ireland. "
        "Check the weather, find flights from Dublin, and suggest activities.",
        mode="concurrent",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    # ─── 6. GRAPH: Packing request routed via WorkflowBuilder ───
    header("6. GRAPH — What should I pack for Tokyo in March?")
    print("User: 'What should I pack for Tokyo in March?'\n")
    await run_workflow(
        "What should I pack for Tokyo in March?",
        mode="graph",
        log_file=log_file,
        trace_dir=trace_dir,
    )

    header("DEMO COMPLETE")
    print(f"📝 Event logs: {log_file}")
    print(f"📄 JSON traces: {trace_dir}/")
    print("   Each trace has: input, agent instructions, tool calls, outputs, timing.")
    print("   Feed these to your evaluator/judge for prompt refinement.\n")


if __name__ == "__main__":
    asyncio.run(main())