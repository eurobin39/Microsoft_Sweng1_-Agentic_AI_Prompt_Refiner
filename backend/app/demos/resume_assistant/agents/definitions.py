"""
Agent definitions for the Resume Assistant.

Dynamically adapts to both older and newer versions of the agent_framework.
"""

import json
import agent_framework
from agent_framework.azure import AzureOpenAIChatClient

# ==========================================
# Version-Safe Imports & Resolvers
# ==========================================

# 1. Safely resolve the Agent class across versions
if hasattr(agent_framework, "ChatAgent"):
    BaseAgent = getattr(agent_framework, "ChatAgent")
elif hasattr(agent_framework, "Agent"):
    BaseAgent = getattr(agent_framework, "Agent")
elif hasattr(agent_framework, "RawAgent"):
    BaseAgent = getattr(agent_framework, "RawAgent")
else:
    raise ImportError("Could not find a valid Agent class in agent_framework")

# 2. Safely resolve the tool decorator across versions
if hasattr(agent_framework, "tool"):
    ai_tool = getattr(agent_framework, "tool")
else:
    # Fallback dummy decorator for newer versions that natively support Python functions
    def ai_tool(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

# ==========================================
# Tools
# ==========================================

@ai_tool(name="save_user_profile", description="Save the user profile data.")
def save_user_profile(contact_info: str, skills: list[str], work_history: list[str], education: list[str]) -> str:
    """Structure and save the extracted user profile data."""
    profile_data = {
        "status": "Success",
        "contact_info": contact_info,
        "skills": skills,
        "work_history": work_history,
        "education": education
    }
    return json.dumps(profile_data, ensure_ascii=False)

@ai_tool(name="format_job_requirements", description="Format the target company's core requirements.")
def format_job_requirements(role_type: str, core_skills: list[str]) -> str:
    """Structure and save the target company's job requirements."""
    company_data = {
        "target_company_data_extracted": True,
        "role_type": role_type,
        "required_skills": core_skills,
    }
    return json.dumps(company_data, ensure_ascii=False)

@ai_tool(name="generate_document_file", description="Output the finalized resume.")
def generate_document_file(final_text: str, format_style: str = "markdown") -> str:
    """Format the final resume output."""
    if format_style.lower() == "latex":
        return f"\\documentclass{{article}}\n\\begin{{document}}\n{final_text}\n\\end{{document}}"
    else:
        return f"# Professional Resume\n\n{final_text}"

@ai_tool(name="record_feedback_score", description="Record the final score and feedback.")
def record_feedback_score(score: int, strengths: str, improvements: str) -> str:
    """Structure and save the review feedback."""
    feedback = {
        "final_mark": f"{score}/100",
        "pass_ats": score >= 75,
        "strengths": strengths,
        "improvements": improvements
    }
    return json.dumps(feedback, indent=2, ensure_ascii=False)

# ==========================================
# Agent Factories
# ==========================================

def create_safe_agent(name: str, instructions: str, chat_client: AzureOpenAIChatClient, tools: list):
    """Helper to instantiate the agent regardless of version specific kwargs."""
    try:
        return BaseAgent(name=name, instructions=instructions, client=chat_client, tools=tools)
    except TypeError:
        return BaseAgent(name=name, instructions=instructions, chat_client=chat_client, tools=tools)

def create_resume_info_collector_agent(chat_client: AzureOpenAIChatClient):
    """Creates the information collector agent."""
    return create_safe_agent(
        name="info_collector_agent",
        instructions=(
            "You are the Resume Info Collector (Step 1). Read the user's raw input. "
            "Extract their contact info, skills, work history, and education. "
            "You MUST call `save_user_profile` to structure and save this data."
        ),
        chat_client=chat_client,
        tools=[save_user_profile],
    )

def create_resume_analysis_agent(chat_client: AzureOpenAIChatClient):
    """Creates the job analysis agent."""
    return create_safe_agent(
        name="job_analyst_agent",
        instructions=(
            "You are the Job Analyst (Step 2). Read the provided Job Description (JD). "
            "Analyze the core role type and the mandatory hard skills. "
            "You MUST call `format_job_requirements` to save your analysis."
        ),
        chat_client=chat_client,
        tools=[format_job_requirements],
    )

def create_resume_writing_agent(chat_client: AzureOpenAIChatClient):
    """Creates the resume writer agent."""
    return create_safe_agent(
        name="resume_writer_agent",
        instructions=(
            "You are the Resume Writer (Step 3). Using the structured user profile and the job requirements, "
            "draft a professional, tailored resume. "
            "Ask the user if they prefer 'markdown' or 'latex'. "
            "Once drafted, you MUST call `generate_document_file` to output the final text."
        ),
        chat_client=chat_client,
        tools=[generate_document_file],
    )

def create_resume_feedback_agent(chat_client: AzureOpenAIChatClient):
    """Creates the feedback agent."""
    return create_safe_agent(
        name="feedback_agent",
        instructions=(
            "You are the Feedback Agent (Step 4). Review the generated resume against the target job requirements. "
            "Evaluate its ATS compatibility. Give it a score (0-100), note its strengths, and suggest improvements. "
            "You MUST call `record_feedback_score` to log your evaluation."
        ),
        chat_client=chat_client,
        tools=[record_feedback_score],
    )