"""
Resume Assistant — main runner.

Provides a unified interface for running the full pipeline with structured tracing.
Agents are called directly so we can record start/end times around each call.
"""

import logging
from typing import Any

from .agents import collect_info, analyze_job, write_resume, review_resume
from .logger import WorkflowTracer, setup_logging


def run_workflow(
    user_input: str,
    job_description: str,
    log_file: str | None = None,
    trace_dir: str = "resume_assistant/log/traces",
) -> dict[str, Any]:
    """
    Run the resume assistant full pipeline with structured tracing.

    Args:
        user_input: The user's resume text or details.
        job_description: The target job description.
        log_file: Optional path for log file.
        trace_dir: Directory to save JSON traces.

    Returns:
        The full trace dict (also saved to trace_dir as JSON).
    """
    setup_logging(level=logging.INFO, log_file=log_file)

    tracer = WorkflowTracer(user_input=user_input, mode="graph")

    tracer.start_agent("resume_info_collector")
    user_profile = collect_info(user_input)
    tracer.end_agent("resume_info_collector", user_profile)

    tracer.start_agent("resume_job_analyzer")
    job_analysis = analyze_job(job_description)
    tracer.end_agent("resume_job_analyzer", job_analysis)

    tracer.start_agent("resume_writer")
    resume = write_resume(user_profile, job_analysis)
    tracer.end_agent("resume_writer", resume)

    tracer.start_agent("resume_reviewer")
    feedback = review_resume(resume, job_analysis)
    tracer.end_agent("resume_reviewer", feedback)

    sections = [
        f"## User Profile\n{user_profile}",
        f"## Job Analysis\n{job_analysis}",
        f"## Generated Resume\n{resume}",
        f"## Resume Feedback\n{feedback}",
    ]
    final_output = "\n\n".join(sections)
    tracer.set_final_output(final_output)
    tracer.save(trace_dir)
    tracer.print_summary()

    return tracer.get_trace()


def run_sync(
    user_input: str,
    job_description: str,
    log_file: str | None = None,
    trace_dir: str = "traces",
) -> dict[str, Any]:
    """Synchronous wrapper (run_workflow is already synchronous; kept for API consistency)."""
    return run_workflow(user_input, job_description, log_file, trace_dir)
