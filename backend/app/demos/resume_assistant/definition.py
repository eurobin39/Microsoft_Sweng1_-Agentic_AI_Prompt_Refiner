from agent_framework import tool
from agent_framework_utils import run_workflow_sync
from .agents import collect_info, analyze_job, write_resume, review_resume
from .workflows.graph import build_graph_workflow

_graph_workflow = None


@tool
def collect_info_tool(user_input: str) -> str:
    """Extract structured resume data from the user's input."""
    return collect_info(user_input, stream=False)


@tool
def analyze_job_tool(job_description: str) -> str:
    """Analyze a job description into structured requirements."""
    return analyze_job(job_description, stream=False)


@tool
def write_resume_tool(user_profile: str, job_analysis: str) -> str:
    """Write a tailored resume in LaTeX given profile and job analysis."""
    return write_resume(user_profile, job_analysis, stream=False)


@tool
def review_resume_tool(resume_content: str, job_analysis: str) -> str:
    """Review a resume against job requirements and provide feedback."""
    return review_resume(resume_content, job_analysis, stream=False)


def _get_graph_workflow():
    global _graph_workflow
    if _graph_workflow is None:
        _graph_workflow = build_graph_workflow()
    return _graph_workflow


def _messages_to_text(messages) -> str:
    if not messages:
        return ""
    if isinstance(messages, str):
        return messages
    parts = []
    for msg in messages:
        text = getattr(msg, "text", None) or getattr(msg, "content", None)
        parts.append(text if text is not None else str(msg))
    return "\n\n".join(parts)


def orchestrator(user_input: str, job_description: str, stream: bool = False) -> str:
    prompt = (
        "User request:\n"
        f"{user_input}\n\n"
        f"Job description provided: {'Yes' if job_description else 'No'}\n\n"
        "Job description:\n"
        f"{job_description}\n\n"
        "Choose the best workflow and respond with the appropriate output."
    )
    payload = {
        "user_input": user_input,
        "job_description": job_description,
    }
    outputs = run_workflow_sync(_get_graph_workflow(), payload)
    response = _messages_to_text(outputs)
    if stream:
        print(response)
    return response
