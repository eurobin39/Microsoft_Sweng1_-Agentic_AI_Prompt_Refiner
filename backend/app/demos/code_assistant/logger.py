"""
Structured Tracing for the code assistant — event-driven, mirrors travel_assistant format.

Hooks into agent_framework streaming events to capture:
  - Tool calls (name, arguments, result)
  - Agent text output
  - Handoffs between agents
  - Timing per agent and total
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

from agent_framework import (
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
    HandoffSentEvent,
    WorkflowOutputEvent,
)

logger = logging.getLogger("code_assistant")


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    if logger.handlers:
        return
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.setLevel(level)


_AGENT_INSTRUCTIONS = {
    "code_triage": (
        "Read the user's request and hand off to the right specialist: "
        "code_explainer, code_refactor, or code_documenter."
    ),
    "code_explainer": (
        "Explain what the code does in plain English using extract_functions and analyze_code_metrics."
    ),
    "code_refactor": (
        "Refactor the code to be cleaner using extract_functions and analyze_code_metrics. "
        "Hand off to code_documenter if documentation is also requested."
    ),
    "code_documenter": (
        "Add docstrings and comments using check_docstrings and extract_functions."
    ),
}

_AGENT_TOOLS = {
    "code_triage": [],
    "code_explainer": ["extract_functions", "analyze_code_metrics"],
    "code_refactor": ["extract_functions", "analyze_code_metrics"],
    "code_documenter": ["check_docstrings", "extract_functions"],
}


class WorkflowTracer:
    def __init__(self, user_input: str, mode: str) -> None:
        self.trace: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "input": user_input,
            "agents": {},
            "execution_order": [],
            "handoffs": [],
            "final_output": "",
            "duration_ms": None,
        }
        self._current_agent: str | None = None
        self._response_buffers: dict[str, list[str]] = {}
        self._start_time = datetime.now()
        self._agent_start_times: dict[str, datetime] = {}
        self._seen_tool_calls: set[str] = set()
        self.event_count = 0

    def _ensure_agent(self, name: str) -> None:
        if name and name not in self.trace["agents"]:
            self.trace["agents"][name] = {
                "instructions": _AGENT_INSTRUCTIONS.get(name, ""),
                "tools_available": _AGENT_TOOLS.get(name, []),
                "tool_calls": [],
                "output": "",
                "duration_ms": None,
            }

    def capture(self, event: Any) -> None:
        self.event_count += 1

        if isinstance(event, ExecutorInvokedEvent):
            executor_id = event.executor_id
            self._current_agent = executor_id
            self._agent_start_times[executor_id or "?"] = datetime.now()
            if executor_id:
                self._ensure_agent(executor_id)
                if executor_id not in self.trace["execution_order"]:
                    self.trace["execution_order"].append(executor_id)

        elif isinstance(event, ExecutorCompletedEvent):
            executor_id = event.executor_id
            start = self._agent_start_times.pop(executor_id or "?", None)
            dur = round((datetime.now() - start).total_seconds() * 1000) if start else None
            if executor_id and executor_id in self.trace["agents"]:
                if dur and dur > 10:
                    self.trace["agents"][executor_id]["duration_ms"] = dur
                if executor_id in self._response_buffers:
                    text = "".join(self._response_buffers.pop(executor_id))
                    if text.strip():
                        self.trace["agents"][executor_id]["output"] = text
            if dur and dur > 10:
                logger.info("✓ %s completed (%sms)", executor_id, dur)

        elif isinstance(event, HandoffSentEvent):
            source = getattr(event, "source", None)
            target = getattr(event, "target", None)
            self.trace["handoffs"].append({"from": str(source), "to": str(target)})
            logger.info("🔀 Handoff: %s → %s", source, target)

        elif isinstance(event, AgentRunUpdateEvent):
            data = event.data
            executor_id = event.executor_id or self._current_agent

            if isinstance(data, AgentResponseUpdate):
                text = getattr(data, "text", "") or ""
                if text and executor_id:
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
                            self._ensure_agent(executor_id or "unknown")
                            tool_entry = {
                                "tool": name,
                                "arguments": _safe_serialise(arguments),
                                "result": None,
                            }
                            if executor_id and executor_id in self.trace["agents"]:
                                self.trace["agents"][executor_id]["tool_calls"].append(tool_entry)
                            logger.info("🔧 %s → %s(%s)", executor_id, name, _truncate(str(arguments), 60))

                    if result is not None and executor_id and executor_id in self.trace["agents"]:
                        for tc in reversed(self.trace["agents"][executor_id]["tool_calls"]):
                            if tc["result"] is None:
                                tc["result"] = _safe_serialise(result)
                                logger.info("   ← %s result: %s", tc["tool"], _truncate(str(result), 80))
                                break

    def set_final_output(self, output: str) -> None:
        self.trace["final_output"] = output
        self.trace["duration_ms"] = round(
            (datetime.now() - self._start_time).total_seconds() * 1000
        )
        for agent_name, chunks in self._response_buffers.items():
            if agent_name in self.trace["agents"] and not self.trace["agents"][agent_name]["output"]:
                text = "".join(chunks)
                if text.strip():
                    self.trace["agents"][agent_name]["output"] = text
        self._response_buffers.clear()

        inactive = [
            name for name, agent in self.trace["agents"].items()
            if not agent["output"] and not agent["tool_calls"] and not agent["duration_ms"]
        ]
        for name in inactive:
            del self.trace["agents"][name]
            if name in self.trace["execution_order"]:
                self.trace["execution_order"].remove(name)

    def save(self, trace_dir: str = "traces") -> str:
        os.makedirs(trace_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{trace_dir}/trace_{self.trace['mode']}_{ts}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.trace, f, indent=2, ensure_ascii=False, default=str)
        logger.info("📄 Trace saved: %s", filename)
        return filename

    def get_trace(self) -> dict[str, Any]:
        return self.trace

    def print_summary(self) -> None:
        t = self.trace
        print(f"\n{'─' * 60}")
        print(f"📊 TRACE SUMMARY — {t['mode'].upper()}")
        print(f"{'─' * 60}")
        print(f"Input:    {t['input']}")
        print(f"Duration: {t['duration_ms']}ms")
        print(f"Agents:   {' → '.join(t['execution_order'])}")
        if t["handoffs"]:
            chain = " → ".join(f"{h['from']}→{h['to']}" for h in t["handoffs"])
            print(f"Handoffs: {chain}")
        print()

        for name in t["execution_order"]:
            agent = t["agents"].get(name, {})
            dur = agent.get("duration_ms")
            print(f"  🤖 {name}" + (f" ({dur}ms)" if dur else ""))
            instr = agent.get("instructions", "")
            if instr:
                print(f"     📋 {_truncate(instr, 100)}")
            for tc in agent.get("tool_calls", []):
                print(f"     🔧 {tc['tool']}({_truncate(str(tc['arguments']), 50)})")
                if tc.get("result"):
                    print(f"        → {_truncate(str(tc['result']), 80)}")
            output = agent.get("output", "")
            if output:
                print(f"     💬 {_truncate(output, 150)}")
            print()

        if t["final_output"]:
            print(f"Final: {_truncate(t['final_output'], 200)}")
        print(f"{'─' * 60}\n")


def _safe_serialise(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialise(v) for v in obj]
    try:
        return json.loads(str(obj))
    except (json.JSONDecodeError, TypeError):
        return str(obj)


def _truncate(text: str, max_len: int = 100) -> str:
    text = text.replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text
