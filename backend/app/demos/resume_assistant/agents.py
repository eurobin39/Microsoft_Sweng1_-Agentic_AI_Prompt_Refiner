from __future__ import annotations

from agent_framework_utils import create_agent, run_agent_sync

_agent_collector = None
_agent_analyzer = None
_agent_writer = None
_agent_reviewer = None


def _get_collector():
    global _agent_collector
    if _agent_collector is None:
        _agent_collector = create_agent(
            name="resume_info_collector",
            instructions=(
                "Pull out the person's info from their resume. "
                "Return as JSON with name, education, skills, experience, projects."
            ),
        )
    return _agent_collector


def _get_analyzer():
    global _agent_analyzer
    if _agent_analyzer is None:
        _agent_analyzer = create_agent(
            name="resume_job_analyzer",
            instructions=(
                "Read the job description and extract the key requirements. Return as JSON."
            ),
        )
    return _agent_analyzer


def _get_writer():
    global _agent_writer
    if _agent_writer is None:
        _agent_writer = create_agent(
            name="resume_writer",
            instructions=(
                "Write a resume based on the person's profile and the job they're applying for."
            ),
        )
    return _agent_writer


def _get_reviewer():
    global _agent_reviewer
    if _agent_reviewer is None:
        _agent_reviewer = create_agent(
            name="resume_reviewer",
            instructions=(
                "Review the resume against the job requirements. "
                "Give a score out of 10 and list what's good and what needs improving."
            ),
        )
    return _agent_reviewer


def get_collector_agent():
    return _get_collector()


def get_analyzer_agent():
    return _get_analyzer()


def get_writer_agent():
    return _get_writer()


def get_reviewer_agent():
    return _get_reviewer()


def collect_info(user_input: str, stream: bool = False) -> str:
    response = run_agent_sync(_get_collector(), f"User Input: {user_input}")
    clean_response = response.replace("```json", "").replace("```", "").strip()
    if "{" in clean_response and "}" in clean_response:
        clean_response = clean_response[clean_response.find("{") : clean_response.rfind("}") + 1]
    if stream:
        print(clean_response)
    return clean_response


def analyze_job(job_description: str, stream: bool = False) -> str:
    response = run_agent_sync(_get_analyzer(), f"Job Description: {job_description}")
    clean_response = response.replace("```json", "").replace("```", "").strip()
    if stream:
        print(clean_response)
    return clean_response


def write_resume(user_profile: str, job_analysis: str, stream: bool = False) -> str:
    response = run_agent_sync(
        _get_writer(),
        f"User Profile: {user_profile}\n\nJob Analysis Requirements: {job_analysis}",
    )
    clean = response.replace("```latex", "").replace("```", "").strip()
    if stream:
        print(clean)
    return clean


def review_resume(resume_content: str, job_analysis: str, stream: bool = False) -> str:
    response = run_agent_sync(
        _get_reviewer(),
        f"Resume Content:\n{resume_content}\n\nJob Requirements:\n{job_analysis}",
    )
    if stream:
        print(response)
    return response
