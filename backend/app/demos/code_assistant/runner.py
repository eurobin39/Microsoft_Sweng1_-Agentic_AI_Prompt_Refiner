"""
Code Assistant — main runner.

Provides a unified interface for running the graph workflow with structured tracing.
Agents are called directly so we can record start/end times around each call.
"""

import asyncio
import logging
from typing import Any

from .agents import explain_code, refactor_code, document_code
from .logger import WorkflowTracer, setup_logging

_VALID_MODES = ("EXPLAIN", "REFACTOR", "DOCUMENT", "REFACTOR_DOCUMENT")


def run_workflow(
    user_request: str,
    code: str,
    mode: str = "EXPLAIN",
    log_file: str | None = None,
    trace_dir: str = "code_assistant/log/traces",
) -> dict[str, Any]:
    """
    Run a code assistant workflow with structured tracing.

    Args:
        user_request: The user's request (used for routing context).
        code: The source code to process.
        mode: Operation mode — "EXPLAIN", "REFACTOR", "DOCUMENT", or "REFACTOR_DOCUMENT".
        log_file: Optional path for log file.
        trace_dir: Directory to save JSON traces.

    Returns:
        The full trace dict (also saved to trace_dir as JSON).
    """
    setup_logging(level=logging.INFO, log_file=log_file)

    mode = mode.upper()
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown mode: {mode!r}. Choose from {_VALID_MODES}.")

    tracer = WorkflowTracer(user_input=user_request, mode="graph")

    final_sections: list[str] = []

    if mode == "EXPLAIN":
        tracer.start_agent("code_explainer")
        explanation = explain_code(code)
        tracer.end_agent("code_explainer", explanation)
        final_sections.append(f"## Explanation\n{explanation}")

    elif mode == "REFACTOR":
        tracer.start_agent("code_refactor")
        refactored = refactor_code(code)
        tracer.end_agent("code_refactor", refactored)
        final_sections.append(f"## Refactored Code\n{refactored}")

    elif mode == "DOCUMENT":
        tracer.start_agent("code_documenter")
        documented = document_code(code)
        tracer.end_agent("code_documenter", documented)
        final_sections.append(f"## Documented Code\n{documented}")

    elif mode == "REFACTOR_DOCUMENT":
        tracer.start_agent("code_refactor")
        refactored = refactor_code(code)
        tracer.end_agent("code_refactor", refactored)

        tracer.start_agent("code_documenter")
        documented = document_code(refactored)
        tracer.end_agent("code_documenter", documented)

        final_sections.append(f"## Refactored Code\n{refactored}")
        final_sections.append(f"## Documented Code\n{documented}")

    final_output = "\n\n".join(final_sections)
    tracer.set_final_output(final_output)
    tracer.save(trace_dir)
    tracer.print_summary()

    return tracer.get_trace()


def run_sync(
    user_request: str,
    code: str,
    mode: str = "EXPLAIN",
    log_file: str | None = None,
    trace_dir: str = "traces",
) -> dict[str, Any]:
    """Synchronous wrapper (run_workflow is already synchronous; kept for API consistency)."""
    return run_workflow(user_request, code, mode, log_file, trace_dir)
