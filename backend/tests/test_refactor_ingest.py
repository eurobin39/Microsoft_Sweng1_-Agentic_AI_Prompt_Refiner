import pytest

from app.services.refactor_ingest import normalize_refactor_payload


@pytest.mark.asyncio
async def test_normalize_refactor_payload_synthesizes_blueprint_and_fallback_trace():
    payload = {
        "agent_name": "copilot_agent",
        "system_prompt": "You are a code assistant.",
        "test_inputs": ["Refactor this function to reduce complexity."],
        "tools": [{"name": "search_code"}],  # intentionally partial tool spec
    }

    blueprint, traces, notes = await normalize_refactor_payload(payload)

    assert blueprint.agent.name == "copilot_agent"
    assert blueprint.agent.system_prompt == "You are a code assistant."
    assert blueprint.agent.tools[0].name == "search_code"
    assert len(blueprint.test_cases) == 1
    assert len(traces) == 1
    assert traces[0].execution_order == ["copilot_agent"]
    assert any("Synthesized blueprint" in n for n in notes)
    assert any("generated one fallback trace" in n.lower() for n in notes)


@pytest.mark.asyncio
async def test_normalize_refactor_payload_accepts_explicit_blueprint_and_trace():
    payload = {
        "blueprint": {
            "agent": {"name": "explicit_agent", "system_prompt": "Be precise."},
            "test_cases": [{"input": "hello"}],
        },
        "traces": [
            {
                "timestamp": "2026-01-01T10:00:00",
                "mode": "sequential",
                "input": "hello",
                "agents": {
                    "explicit_agent": {
                        "instructions": "Be precise.",
                        "tools_available": [],
                        "tool_calls": [],
                        "output": "hello",
                    }
                },
                "execution_order": ["explicit_agent"],
                "handoffs": [],
                "final_output": "hello",
            }
        ],
    }

    blueprint, traces, notes = await normalize_refactor_payload(payload)

    assert blueprint.agent.name == "explicit_agent"
    assert len(traces) == 1
    assert traces[0].input == "hello"
    assert any("Using explicit blueprint" in n for n in notes)
