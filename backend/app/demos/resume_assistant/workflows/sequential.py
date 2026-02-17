"""
Sequential Workflow — chained agent pipeline.

This version uses WorkflowBuilder and calls the agents by their original names.
"""

from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient

from ..agents import (
    create_resume_info_collector_agent,
    create_resume_analysis_agent,
    create_resume_writing_agent,
    create_resume_feedback_agent,
)

def build_sequential_workflow(chat_client: AzureOpenAIChatClient):
    """Build the sequential workflow pipeline."""
    info = create_resume_info_collector_agent(chat_client)
    job = create_resume_analysis_agent(chat_client)
    writer = create_resume_writing_agent(chat_client)
    feedback = create_resume_feedback_agent(chat_client)

    builder = WorkflowBuilder(
        name="resume_assistant_sequential",
        description="MAF Resume Assistant: collect -> analyze -> write -> review",
        start_executor=info,
        output_executors=[feedback],
    )

    # Link ALL agents into a single continuous chain, starting from 'info'
    builder.add_chain([info, job, writer, feedback])
    
    return builder.build()