# 2nd Step.
# Analysis Agent - Analyze job postings
# input - job posting text -> output - key requirements, skills, qualifications (structured data)

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)


def analyze_job(job_description: str, stream: bool = False) -> str:
    """Takes a job description and returns structured JSON with key requirements, skills, and qualifications."""

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are an expert Job Analyst.
Analyze the JD and output a STRICT JSON summary.

Output Format (JSON only):
{
    "role": "Job Title",
    "required_skills": ["list of hard skills"],
    "preferred_skills": ["list of nice-to-have skills"],
    "keywords": ["ATS keywords"],
    "experience_level": "Junior/Mid/Senior",
    "domain": "Industry/Sector"
}

Do not include markdown formatting. Just return the raw JSON string."""
            },
            {
                "role": "user",
                "content": f"Job Description: {job_description}"
            }
        ],
        max_completion_tokens=2048
    )

    if stream:
        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()
        clean_response = full_response.replace("```json", "").replace("```", "").strip()
        return clean_response
    else:
        raw = response.choices[0].message.content
        print(raw)
        clean_response = raw.replace("```json", "").replace("```", "").strip()
        return clean_response