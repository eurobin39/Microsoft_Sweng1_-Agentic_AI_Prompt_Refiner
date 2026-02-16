"""
Sequential Workflow — chained agent pipeline.

Uses SequentialBuilder from agent_framework.
Each agent processes in turn, with full conversation history passed
to the next agent in the sequence.  

Use case:
- User provides background + job posting
- InfoCollector extracts structured profile
- JobAnalyst extracts job requirements + keywords
- ResumeWriter writes a tailored resume
- ResumeReviewer scores and suggests improvements

Architecture:
    User Request → InfoCollectorAgent → JobAnalystAgent → ResumeWriterAgent → ResumeReviewerAgent → Output
    (each agent Sees the full conversation so far)
"""

from agent_framework import SequentialBuilder
from agent_framework.azure import AzureOpenAIChatClient

from ..agents.definitions import (
    create_info_collector_agent,
    create_job_analyst_agent,
    create_resume_writer_agent,
    create_resume_reviewer_agent,
)


def build_sequential_workflow(chat_client: AzureOpenAIChatClient):
    """
    Build a sequential workflow:
        collect → analyze → write → review

    Later agents see earlier agents' outputs in the conversation history,
    so writing and review are job-specific and consistent.
    """
    info = create_info_collector_agent(chat_client)
    job = create_job_analyst_agent(chat_client)
    writer = create_resume_writer_agent(chat_client)
    reviewer = create_resume_reviewer_agent(chat_client)

    workflow = (
        SequentialBuilder()
        .participants([info, job, writer, reviewer])
        .build()
    )

    return workflow
