from __future__ import annotations

from typing import Any

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from agent_framework_utils import create_agent
from ..agents import collect_info, analyze_job, write_resume, review_resume


def _mode_is(*modes: str):
    def _cond(message: Any) -> bool:
        return isinstance(message, dict) and message.get("mode") in modes

    return _cond


def _ensure_payload(message: Any) -> dict:
    if isinstance(message, dict):
        return dict(message)
    return {"user_input": str(message), "job_description": ""}


@executor(id="route_request")
async def route_request(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    selector = create_agent(
        name="resume_assistant_router",
        instructions=(
            "Decide which workflow to use for a resume request.\n"
            "Return ONLY one of: FULL_PIPELINE, WRITE_ONLY, REVIEW_ONLY, ANALYZE_ONLY."
        ),
    )
    prompt = (
        "Choose workflow for this request. Return ONLY FULL_PIPELINE, WRITE_ONLY, REVIEW_ONLY, or ANALYZE_ONLY.\n\n"
        f"User request:\n{payload.get('user_input','')}\n\n"
        f"Job description provided: {'Yes' if payload.get('job_description') else 'No'}\n\n"
        f"Job description:\n{payload.get('job_description','')}\n"
    )
    mode = (await selector.run(prompt)).text.strip().upper()
    payload["mode"] = mode
    await ctx.send_message(payload)


@executor(id="collect_info")
async def collect_info_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["user_profile"] = collect_info(payload.get("user_input", ""))
    await ctx.send_message(payload)


@executor(id="analyze_job")
async def analyze_job_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["job_analysis"] = analyze_job(payload.get("job_description", ""))
    await ctx.send_message(payload)


@executor(id="write_resume")
async def write_resume_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["resume"] = write_resume(
        payload.get("user_profile", ""),
        payload.get("job_analysis", ""),
    )
    await ctx.send_message(payload)


@executor(id="review_resume")
async def review_resume_node(message: dict, ctx: WorkflowContext[dict]) -> None:
    payload = _ensure_payload(message)
    payload["feedback"] = review_resume(
        payload.get("resume", ""),
        payload.get("job_analysis", ""),
    )
    await ctx.send_message(payload)


@executor(id="emit_output")
async def emit_output_node(message: dict, ctx: WorkflowContext[None, str]) -> None:
    payload = _ensure_payload(message)
    mode = payload.get("mode", "FULL_PIPELINE")
    sections: list[str] = []

    if mode == "FULL_PIPELINE":
        sections.append(f"## User Profile\n{payload.get('user_profile','')}")
        sections.append(f"## Job Analysis\n{payload.get('job_analysis','')}")
        sections.append(f"## Generated Resume\n{payload.get('resume','')}")
        sections.append(f"## Resume Feedback\n{payload.get('feedback','')}")
    elif mode == "WRITE_ONLY":
        sections.append(f"## Job Analysis\n{payload.get('job_analysis','')}")
        sections.append(f"## Generated Resume\n{payload.get('resume','')}")
    elif mode == "REVIEW_ONLY":
        sections.append(f"## Job Analysis\n{payload.get('job_analysis','')}")
        sections.append(f"## Resume Feedback\n{payload.get('feedback','')}")
    else:
        sections.append(f"## Job Analysis\n{payload.get('job_analysis','')}")

    await ctx.yield_output("\n\n".join(sections))


def build_graph_workflow():
    router = route_request
    collector = collect_info_node
    analyzer = analyze_job_node
    writer = write_resume_node
    reviewer = review_resume_node
    output = emit_output_node

    builder = WorkflowBuilder(start_executor=router)

    builder.add_edge(router, collector, condition=_mode_is("FULL_PIPELINE"))
    builder.add_edge(router, analyzer, condition=_mode_is("WRITE_ONLY", "REVIEW_ONLY", "ANALYZE_ONLY"))

    builder.add_edge(collector, analyzer)
    builder.add_edge(analyzer, writer, condition=_mode_is("FULL_PIPELINE", "WRITE_ONLY"))
    builder.add_edge(analyzer, reviewer, condition=_mode_is("REVIEW_ONLY"))
    builder.add_edge(analyzer, output, condition=_mode_is("ANALYZE_ONLY"))

    builder.add_edge(writer, reviewer, condition=_mode_is("FULL_PIPELINE"))
    builder.add_edge(writer, output, condition=_mode_is("WRITE_ONLY"))
    builder.add_edge(reviewer, output, condition=_mode_is("FULL_PIPELINE", "REVIEW_ONLY"))

    return builder.build()
