"""
Structured Tracing for the resume assistant.

Manual trace building — runner.py calls agents directly and records:
  - start_agent(name): records start time, adds agent to execution_order
  - end_agent(name, output): records duration and output
  - save(trace_dir): JSON trace matching travel_assistant format

Output format (identical to travel_assistant WorkflowTracer):
{
  "timestamp": "...", "mode": "graph", "input": "...",
  "agents": {
    "agent_name": {
      "instructions": "...", "tools_available": [],
      "tool_calls": [], "output": "...", "duration_ms": 1200
    }
  },
  "execution_order": [...], "handoffs": [],
  "final_output": "...", "duration_ms": 2500
}
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger("resume_assistant")


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    """Configure logging with console and optional file output."""
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
    "resume_info_collector": "Extract information from the resume.",
    "resume_job_analyzer": "Read the job description and list the requirements.",
    "resume_writer": "Write a resume.",
    "resume_reviewer": "Review the resume and provide feedback.",
}

_AGENT_TOOLS: dict[str, list] = {
    "resume_info_collector": [],
    "resume_job_analyzer": [],
    "resume_writer": [],
    "resume_reviewer": [],
}


class WorkflowTracer:
    """
    Manual trace builder for resume assistant runs.

    Runner calls start_agent/end_agent directly around each agent call,
    producing a JSON trace that matches the travel_assistant format.
    """

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
        self._start_time = datetime.now()
        self._agent_start_times: dict[str, datetime] = {}

    def start_agent(self, name: str) -> None:
        """Record that an agent has started."""
        if name not in self.trace["agents"]:
            self.trace["agents"][name] = {
                "instructions": _AGENT_INSTRUCTIONS.get(name, ""),
                "tools_available": _AGENT_TOOLS.get(name, []),
                "tool_calls": [],
                "output": "",
                "duration_ms": None,
            }
        if name not in self.trace["execution_order"]:
            self.trace["execution_order"].append(name)
        self._agent_start_times[name] = datetime.now()
        logger.info("▶ %s started", name)

    def end_agent(self, name: str, output: str) -> None:
        """Record that an agent has finished with its output."""
        start = self._agent_start_times.pop(name, None)
        dur = round((datetime.now() - start).total_seconds() * 1000) if start else None
        if name in self.trace["agents"]:
            self.trace["agents"][name]["output"] = output
            if dur:
                self.trace["agents"][name]["duration_ms"] = dur
        logger.info("✓ %s completed (%sms)", name, dur)

    def set_final_output(self, output: str) -> None:
        """Set the final workflow output and total duration."""
        self.trace["final_output"] = output
        self.trace["duration_ms"] = round(
            (datetime.now() - self._start_time).total_seconds() * 1000
        )

    def save(self, trace_dir: str = "traces") -> str:
        """Save the trace as a JSON file. Returns the file path."""
        os.makedirs(trace_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = self.trace["mode"]
        filename = f"{trace_dir}/trace_{mode}_{ts}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.trace, f, indent=2, ensure_ascii=False, default=str)
        logger.info("📄 Trace saved: %s", filename)
        return filename

    def get_trace(self) -> dict[str, Any]:
        return self.trace

    def print_summary(self) -> None:
        """Print a human-readable summary to console."""
        t = self.trace
        print(f"\n{'─' * 60}")
        print(f"📊 TRACE SUMMARY — {t['mode'].upper()}")
        print(f"{'─' * 60}")
        print(f"Input:    {_truncate(t['input'], 80)}")
        print(f"Duration: {t['duration_ms']}ms")
        print(f"Agents:   {' → '.join(t['execution_order'])}")
        print()

        for name in t["execution_order"]:
            agent = t["agents"].get(name, {})
            dur = agent.get("duration_ms")
            print(f"  🤖 {name}" + (f" ({dur}ms)" if dur else ""))

            instr = agent.get("instructions", "")
            if instr:
                print(f"     📋 {_truncate(instr, 100)}")

            output = agent.get("output", "")
            if output:
                print(f"     💬 {_truncate(output, 150)}")
            print()

        if t["final_output"]:
            print(f"Final: {_truncate(t['final_output'], 200)}")
        print(f"{'─' * 60}\n")


def _truncate(text: str, max_len: int = 100) -> str:
    text = text.replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text
