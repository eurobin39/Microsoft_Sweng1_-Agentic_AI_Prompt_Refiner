# Resume Builder Orchestrator
# Routes user requests through the appropriate resume agents in sequence
# input - user background info + job description -> output - tailored resume with feedback

import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from .resume_info_collector_agent import collect_info
from .resume_analysis_agent import analyze_job
from .resume_writing_agent import write_resume
from .resume_feedback_agent import review_resume

load_dotenv()


def orchestrator(user_input: str, job_description: str, stream: bool = False) -> str:
    """
    Routes the resume building process through specialized agents.

    Analyzes the user's request and determines the workflow:
    - collect_info: Extract structured profile data from user input
    - analyze_job: Parse job description into key requirements
    - write_resume: Generate a tailored resume
    - review_resume: Provide feedback and improvement suggestions
    """

    # Initialize client at function level (lazy loading) to handle missing env vars in CI
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-12-01-preview"
    )

    # Use LLM to classify the intent
    classification_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": """You are a routing assistant for a resume builder system.
Classify the user's request into one of these workflows:
- "full_pipeline": User wants a complete resume built from scratch (collect info -> analyze job -> write resume -> review)
- "write_only": User already has structured profile/job data and just wants a resume written
- "review_only": User already has a resume and just wants feedback against a job description
- "analyze_job": User only wants to analyze a job posting

Respond in this exact format:
INTENT: [full_pipeline|write_only|review_only|analyze_job]"""
            },
            {
                "role": "user",
                "content": f"User request: {user_input}\n\nJob description provided: {'Yes' if job_description else 'No'}"
            }
        ],
        max_completion_tokens=200
    )

    # Parse the classification response
    classification = classification_response.choices[0].message.content
    intent = "full_pipeline"

    for line in classification.strip().split('\n'):
        if line.startswith("INTENT:"):
            intent = line.split(":", 1)[1].strip().lower()

    results = []

    if intent == "full_pipeline":
        # Step 1: Collect and structure user info
        print("📋 Step 1: Collecting user information...\n")
        user_profile = collect_info(user_input, stream=stream)
        results.append(f"## User Profile\n{user_profile}")

        # Step 2: Analyze the job description
        print("\n🔍 Step 2: Analyzing job description...\n")
        job_analysis = analyze_job(job_description, stream=stream)
        results.append(f"## Job Analysis\n{job_analysis}")

        # Step 3: Write the tailored resume
        print("\n✍️ Step 3: Writing tailored resume...\n")
        resume = write_resume(user_profile, job_analysis, stream=stream)
        results.append(f"## Generated Resume\n{resume}")

        # Step 4: Review and provide feedback
        print("\n📝 Step 4: Reviewing resume...\n")
        feedback = review_resume(resume, job_analysis, stream=stream)
        results.append(f"## Resume Feedback\n{feedback}")

    elif intent == "write_only":
        print("✍️ Routing to Resume Writer Agent...\n")
        # Treat user_input as pre-structured profile data
        job_analysis = analyze_job(job_description, stream=stream)
        resume = write_resume(user_input, job_analysis, stream=stream)
        results.append(resume)

    elif intent == "review_only":
        print("📝 Routing to Resume Feedback Agent...\n")
        # Treat user_input as existing resume content
        job_analysis = analyze_job(job_description, stream=stream)
        feedback = review_resume(user_input, job_analysis, stream=stream)
        results.append(feedback)

    elif intent == "analyze_job":
        print("🔍 Routing to Job Analysis Agent...\n")
        job_analysis = analyze_job(job_description, stream=stream)
        results.append(job_analysis)

    else:
        # Fallback: run full pipeline
        print("Intent unclear. Running full pipeline...\n")
        user_profile = collect_info(user_input, stream=stream)
        job_analysis = analyze_job(job_description, stream=stream)
        resume = write_resume(user_profile, job_analysis, stream=stream)
        feedback = review_resume(resume, job_analysis, stream=stream)
        results.append(f"## Generated Resume\n{resume}\n\n## Feedback\n{feedback}")

    # Combine results
    if len(results) > 1:
        combined = "\n\n" + "=" * 80 + "\n\n".join(results)
        return combined
    else:
        return results[0] if results else ""