from __future__ import annotations

import difflib
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

from agent_framework import (
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ChatAgent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
    HandoffSentEvent,
    WorkflowBuilder,
    WorkflowOutputEvent,
    tool,
)

from app.models.models import AgentBlueprint, EvaluationCriteria, TestCase
from app.models.trace_logs import TraceLog


def _safe_serialise(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialise(v) for v in obj]
    try:
        return json.loads(str(obj))
    except Exception:
        return str(obj)


class RuntimeWorkflowTracer:
    def __init__(self, user_input: str, agent_name: str, instructions: str, tools_available: List[str]) -> None:
        self.trace: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "mode": "runtime",
            "input": user_input,
            "agents": {},
            "execution_order": [],
            "handoffs": [],
            "final_output": "",
            "duration_ms": None,
        }
        self._default_agent_name = agent_name
        self._instructions = instructions
        self._tools_available = tools_available
        self._current_agent: str | None = None
        self._response_buffers: Dict[str, List[str]] = {}
        self._agent_start_times: Dict[str, datetime] = {}
        self._start_time = datetime.now()
        self._seen_tool_calls: set[str] = set()

    def _ensure_agent(self, name: str) -> None:
        if not name:
            return
        if name not in self.trace["agents"]:
            self.trace["agents"][name] = {
                "instructions": self._instructions if name == self._default_agent_name else "",
                "tools_available": self._tools_available if name == self._default_agent_name else [],
                "tool_calls": [],
                "output": "",
                "duration_ms": None,
            }

    def capture(self, event: Any) -> None:
        if isinstance(event, ExecutorInvokedEvent):
            executor_id = event.executor_id or self._default_agent_name
            self._current_agent = executor_id
            self._agent_start_times[executor_id] = datetime.now()
            self._ensure_agent(executor_id)
            if executor_id not in self.trace["execution_order"]:
                self.trace["execution_order"].append(executor_id)
            return

        if isinstance(event, ExecutorCompletedEvent):
            executor_id = event.executor_id or self._current_agent or self._default_agent_name
            self._ensure_agent(executor_id)
            started = self._agent_start_times.pop(executor_id, None)
            if started:
                self.trace["agents"][executor_id]["duration_ms"] = round((datetime.now() - started).total_seconds() * 1000)
            if executor_id in self._response_buffers:
                text = "".join(self._response_buffers.pop(executor_id))
                if text.strip():
                    self.trace["agents"][executor_id]["output"] = text
            return

        if isinstance(event, HandoffSentEvent):
            source = getattr(event, "source", None)
            target = getattr(event, "target", None)
            self.trace["handoffs"].append({"from": str(source), "to": str(target)})
            return

        if isinstance(event, AgentRunUpdateEvent):
            data = event.data
            executor_id = event.executor_id or self._current_agent or self._default_agent_name
            self._ensure_agent(executor_id)
            if isinstance(data, AgentResponseUpdate):
                text = getattr(data, "text", "") or ""
                if text:
                    self._response_buffers.setdefault(executor_id, []).append(text)
                for content in (data.contents or []):
                    name = getattr(content, "name", None)
                    arguments = getattr(content, "arguments", None)
                    result = getattr(content, "result", None)
                    call_id = getattr(content, "call_id", None)

                    if name and isinstance(name, str) and name.strip():
                        dedup_key = f"{executor_id}:{call_id or name}"
                        if dedup_key not in self._seen_tool_calls:
                            self._seen_tool_calls.add(dedup_key)
                            self.trace["agents"][executor_id]["tool_calls"].append(
                                {"tool": name, "arguments": _safe_serialise(arguments), "result": None}
                            )
                    if result is not None:
                        for tc in reversed(self.trace["agents"][executor_id]["tool_calls"]):
                            if tc["result"] is None:
                                tc["result"] = _safe_serialise(result)
                                break

    def finalize(self, final_output: str) -> None:
        self.trace["final_output"] = final_output
        self.trace["duration_ms"] = round((datetime.now() - self._start_time).total_seconds() * 1000)
        for agent_name, chunks in list(self._response_buffers.items()):
            if agent_name in self.trace["agents"] and not self.trace["agents"][agent_name]["output"]:
                text = "".join(chunks)
                if text.strip():
                    self.trace["agents"][agent_name]["output"] = text
        self._response_buffers.clear()


def _make_mock_tool(tool_name: str, tool_description: str):
    @tool(name=tool_name, description=tool_description or f"Mock tool for {tool_name}")
    def _mock_tool(**kwargs: Any) -> str:
        return json.dumps(
            {
                "tool": tool_name,
                "status": "ok",
                "mocked": True,
                "arguments": _safe_serialise(kwargs),
            },
            ensure_ascii=False,
        )

    return _mock_tool


def _expected_tools_from_test_case(test_case: TestCase, candidate_tools: List[str]) -> List[str]:
    expected_tools: List[str] = []
    context = test_case.context or {}
    raw = context.get("expected_tool_calls")
    if isinstance(raw, dict):
        for v in raw.values():
            if isinstance(v, list):
                expected_tools.extend([str(name) for name in v])
    elif isinstance(raw, list):
        expected_tools.extend([str(name) for name in raw])
    elif isinstance(raw, str):
        expected_tools.append(raw)

    if not expected_tools and test_case.expected_behavior:
        text = test_case.expected_behavior.lower()
        expected_tools = [t for t in candidate_tools if t.lower() in text]
    return list(dict.fromkeys(expected_tools))


def _keyword_hit_ratio(text: str, expected_behavior: str | None) -> float | None:
    if not expected_behavior:
        return None
    tokens = [t.strip(".,()[]{}:;!?").lower() for t in expected_behavior.split()]
    keywords = [t for t in tokens if len(t) >= 5]
    unique_keywords = list(dict.fromkeys(keywords))[:12]
    if not unique_keywords:
        return None
    target = (text or "").lower()
    hits = sum(1 for kw in unique_keywords if kw in target)
    return hits / len(unique_keywords)


def build_ground_truth_assessment(
    blueprint: AgentBlueprint,
    traces: List[TraceLog],
) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    candidate_tools = [t.name for t in blueprint.agent.tools]
    max_items = min(len(blueprint.test_cases), len(traces))
    for idx in range(max_items):
        test_case = blueprint.test_cases[idx]
        trace = traces[idx]
        final_output = trace.final_output if trace else ""
        output_score = None
        if test_case.expected_output:
            output_score = difflib.SequenceMatcher(None, test_case.expected_output, final_output or "").ratio()

        behavior_score = _keyword_hit_ratio(final_output or "", test_case.expected_behavior)

        expected_tools = _expected_tools_from_test_case(test_case, candidate_tools)
        actual_tools: List[str] = []
        if trace:
            for agent_data in trace.agents.values():
                for call in agent_data.tool_calls:
                    if call.tool:
                        actual_tools.append(call.tool)
        actual_tools = list(dict.fromkeys(actual_tools))
        tool_score = None
        missing_tools: List[str] = []
        if expected_tools:
            missing_tools = [name for name in expected_tools if name not in actual_tools]
            tool_score = (len(expected_tools) - len(missing_tools)) / len(expected_tools)

        components = [s for s in (output_score, behavior_score, tool_score) if s is not None]
        blended_score = sum(components) / len(components) if components else 0.5
        reports.append(
            {
                "test_case_index": idx,
                "description": test_case.description or f"test_case_{idx + 1}",
                "input": test_case.input,
                "score": round(blended_score, 4),
                "output_similarity": round(output_score, 4) if output_score is not None else None,
                "behavior_keyword_score": round(behavior_score, 4) if behavior_score is not None else None,
                "expected_tools": expected_tools,
                "actual_tools": actual_tools,
                "missing_tools": missing_tools,
            }
        )
    return reports


def apply_ground_truth_report_to_blueprint(
    blueprint: AgentBlueprint,
    report: List[Dict[str, Any]],
) -> AgentBlueprint:
    if not report:
        return blueprint
    avg = sum(item["score"] for item in report) / len(report)
    summary = f"Runtime precheck score={avg:.3f}. Consider missing_tools and low-output-similarity cases while judging."
    raw = blueprint.model_dump(mode="json")
    criteria = raw.get("evaluation_criteria") or {"goals": [], "constraints": [], "priority_description": None}
    goals = list(criteria.get("goals") or [])
    if "Respect runtime precheck evidence from generated traces." not in goals:
        goals.append("Respect runtime precheck evidence from generated traces.")
    priority = criteria.get("priority_description")
    criteria["goals"] = goals
    criteria["priority_description"] = f"{priority} {summary}".strip() if priority else summary
    raw["evaluation_criteria"] = EvaluationCriteria.model_validate(criteria).model_dump(mode="json")
    return AgentBlueprint.model_validate(raw)


async def run_blueprint_in_runtime(
    blueprint: AgentBlueprint,
    chat_client: Any,
    *,
    max_test_cases: int | None = None,
) -> Tuple[List[TraceLog], List[str]]:
    notes: List[str] = []
    tool_defs = [_make_mock_tool(t.name, t.description) for t in blueprint.agent.tools]
    if tool_defs:
        notes.append(f"Registered {len(tool_defs)} mock tool(s) for runtime execution.")
    else:
        notes.append("No tools declared in blueprint; runtime execution will be tool-free.")

    limit = len(blueprint.test_cases) if max_test_cases is None else max(0, min(len(blueprint.test_cases), max_test_cases))
    selected_cases = blueprint.test_cases[:limit]
    traces: List[TraceLog] = []

    for idx, case in enumerate(selected_cases):
        agent_name = blueprint.agent.name or "runtime_agent"
        runtime_agent = ChatAgent(
            name=agent_name,
            instructions=blueprint.agent.system_prompt,
            chat_client=chat_client,
            tools=tool_defs,
        )
        workflow = WorkflowBuilder().set_start_executor(runtime_agent).build()
        tracer = RuntimeWorkflowTracer(
            user_input=case.input,
            agent_name=agent_name,
            instructions=blueprint.agent.system_prompt,
            tools_available=[t.name for t in blueprint.agent.tools],
        )

        final_output = ""
        async for event in workflow.run_stream(case.input):
            tracer.capture(event)
            if isinstance(event, WorkflowOutputEvent):
                final_output = getattr(event, "text", "") or str(event)
        tracer.finalize(final_output)
        traces.append(TraceLog.model_validate(tracer.trace))
        notes.append(f"Executed runtime test case {idx + 1}/{limit}.")

    return traces, notes
