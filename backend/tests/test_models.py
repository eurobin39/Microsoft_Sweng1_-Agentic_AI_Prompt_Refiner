import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from app.models.models import AgentBlueprint, AgentInfo, TestCase, EvaluationCriteria, Tool
from app.models.trace_logs import TraceLog, Handoff, AgentLog, ToolCall


# ---------------------------------------------------------------------------
# AgentBlueprint / schema models
# ---------------------------------------------------------------------------

class TestAgentBlueprint:
    """Test that AgentBlueprint parses valid JSON and rejects invalid input."""

    MINIMAL_VALID = {
        "agent": {"system_prompt": "You are helpful."},
        "test_cases": [{"input": "Hello"}],
    }

    FULL_VALID = {
        "agent": {
            "name": "Code Explainer",
            "description": "Explains code in plain English",
            "system_prompt": "You explain code clearly.",
            "model": "gpt-4o",
            "provider": "azure_openai",
            "model_parameters": {"temperature": 0.7, "max_tokens": 500, "top_p": 0.9},
            "tools": [
                {"name": "search_db", "description": "Searches the database", "parameters": {"type": "object"}},
            ],
            "output_format": "text",
        },
        "test_cases": [
            {
                "description": "Simple function",
                "input": "Explain this Python function",
                "expected_output": "This function adds two numbers",
                "expected_behavior": "Should give a clear explanation",
                "context": {"language": "python"},
            }
        ],
        "evaluation_criteria": {
            "goals": ["accuracy", "conciseness"],
            "constraints": ["Must not invent information"],
            "priority_description": "Accuracy matters most",
        },
    }

    def test_minimal_valid(self):
        bp = AgentBlueprint.model_validate(self.MINIMAL_VALID)
        assert bp.agent.system_prompt == "You are helpful."
        assert len(bp.test_cases) == 1
        assert bp.evaluation_criteria is None

    def test_full_valid(self):
        bp = AgentBlueprint.model_validate(self.FULL_VALID)
        assert bp.agent.name == "Code Explainer"
        assert bp.agent.provider.value == "azure_openai"
        assert bp.agent.tools[0].name == "search_db"
        assert bp.evaluation_criteria.goals == ["accuracy", "conciseness"]

    def test_missing_system_prompt_rejected(self):
        data = {"agent": {"name": "No prompt"}, "test_cases": [{"input": "Hi"}]}
        with pytest.raises(ValidationError):
            AgentBlueprint.model_validate(data)

    def test_empty_test_cases_rejected(self):
        data = {"agent": {"system_prompt": "Hello"}, "test_cases": []}
        with pytest.raises(ValidationError):
            AgentBlueprint.model_validate(data)

    def test_missing_test_cases_rejected(self):
        data = {"agent": {"system_prompt": "Hello"}}
        with pytest.raises(ValidationError):
            AgentBlueprint.model_validate(data)

    def test_extra_fields_rejected(self):
        data = {**self.MINIMAL_VALID, "rogue_field": "surprise"}
        with pytest.raises(ValidationError):
            AgentBlueprint.model_validate(data)

    def test_model_parameters_allows_extras(self):
        data = {
            "agent": {
                "system_prompt": "Hi",
                "model_parameters": {"temperature": 0.5, "custom_param": True},
            },
            "test_cases": [{"input": "test"}],
        }
        bp = AgentBlueprint.model_validate(data)
        assert bp.agent.model_parameters.temperature == 0.5

    def test_tool_extra_fields_rejected(self):
        data = {
            "agent": {
                "system_prompt": "Hi",
                "tools": [{"name": "t", "description": "d", "rogue": "bad"}],
            },
            "test_cases": [{"input": "test"}],
        }
        with pytest.raises(ValidationError):
            AgentBlueprint.model_validate(data)

    def test_stringified_json_fields_are_accepted(self):
        data = {
            "agent": {
                "system_prompt": "You are helpful.",
                "model_parameters": "{}",
                "output_schema": "{}",
            },
            "test_cases": [
                {
                    "description": "d",
                    "input": "i",
                    "expected_behavior": "b",
                    "expected_output": "o",
                    "context": "{}",
                }
            ],
            "evaluation_criteria": "{}",
        }

        bp = AgentBlueprint.model_validate(data)
        assert bp.agent.model_parameters == {}
        assert bp.agent.output_schema == {}
        assert bp.test_cases[0].context == {}
        assert bp.evaluation_criteria is not None
        assert bp.evaluation_criteria.goals == []


# ---------------------------------------------------------------------------
# TraceLog models
# ---------------------------------------------------------------------------

TRACE_DIR = Path(__file__).resolve().parent.parent / "app" / "demos" / "travel_assistant" / "log" / "traces"

# Inline fixture — not tied to any specific file on disk
HANDOFF_TRACE_FIXTURE = {
    "timestamp": "2026-02-11T00:05:06.000000",
    "mode": "handoff",
    "input": "What's the weather like in Tokyo?",
    "agents": {
        "triage_agent": {
            "instructions": "Route the user to the right agent.",
            "tools_available": [],
            "tool_calls": [],
            "output": "",
            "duration_ms": None,
        },
        "weather_agent": {
            "instructions": "Tell the user about the weather.",
            "tools_available": ["get_weather"],
            "tool_calls": [
                {"tool": "get_weather", "arguments": "", "result": "Sunny, 18°C"},
            ],
            "output": "It is sunny and 18°C in Tokyo.",
            "duration_ms": 5367,
        },
    },
    "execution_order": ["triage_agent", "weather_agent"],
    "handoffs": [{"from": "triage_agent", "to": "weather_agent"}],
    "final_output": "It is sunny and 18°C in Tokyo.",
    "duration_ms": 7055,
}


class TestTraceLog:
    """Test TraceLog parsing."""

    def test_parse_handoff_trace(self):
        trace = TraceLog.model_validate(HANDOFF_TRACE_FIXTURE)

        assert trace.mode == "handoff"
        assert trace.input == "What's the weather like in Tokyo?"
        assert "triage_agent" in trace.agents
        assert "weather_agent" in trace.agents
        assert trace.execution_order == ["triage_agent", "weather_agent"]
        assert trace.duration_ms == 7055

    def test_handoff_from_to_parsed(self):
        """The critical fix — handoff 'from'/'to' keys must be captured."""
        trace = TraceLog.model_validate(HANDOFF_TRACE_FIXTURE)

        assert len(trace.handoffs) == 1
        handoff = trace.handoffs[0]
        assert handoff.from_agent == "triage_agent"
        assert handoff.to_agent == "weather_agent"

    def test_agent_tool_calls_parsed(self):
        trace = TraceLog.model_validate(HANDOFF_TRACE_FIXTURE)

        weather = trace.agents["weather_agent"]
        assert len(weather.tool_calls) == 1
        assert weather.tool_calls[0].tool == "get_weather"
        assert weather.duration_ms == 5367

    def test_stringified_agents_object_is_accepted(self):
        data = {
            "timestamp": "2026-03-21T00:00:00Z",
            "input": "i",
            "agents": "{}",
            "execution_order": ["main"],
            "duration_ms": "1",
            "mode": "single",
            "final_output": "o",
            "handoffs": [],
        }

        trace = TraceLog.model_validate(data)
        assert trace.agents == {}
        assert trace.duration_ms == 1

    def test_all_trace_files_parse(self):
        """Every trace file in the traces dir should parse without error."""
        trace_files = list(TRACE_DIR.glob("*.json"))
        assert len(trace_files) > 0, "No trace files found"
        for path in trace_files:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            trace = TraceLog.model_validate(data)
            assert trace.timestamp is not None


class TestHandoff:
    """Unit tests for the Handoff model specifically."""

    def test_from_to_aliases(self):
        h = Handoff.model_validate({"from": "agent_a", "to": "agent_b"})
        assert h.from_agent == "agent_a"
        assert h.to_agent == "agent_b"

    def test_python_field_names_also_work(self):
        h = Handoff(from_agent="agent_a", to_agent="agent_b")
        assert h.from_agent == "agent_a"
        assert h.to_agent == "agent_b"

    def test_empty_handoff(self):
        h = Handoff.model_validate({})
        assert h.from_agent is None
        assert h.to_agent is None
