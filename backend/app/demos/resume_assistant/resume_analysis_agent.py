"""
Legacy compatibility wrapper for Job Analysis.

Provides analyze_job(job_description) without requiring MAF wiring.
Client is created lazily (CI-safe import).
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


def _client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-12-01-preview",
    )


def analyze_job(job_description: str, stream: bool = False) -> str:
    response = _client().chat.completions.create(
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

Return ONLY JSON. Do not include markdown fences.""",
            },
            {"role": "user", "content": f"Job Description: {job_description}"},
        ],
        max_completion_tokens=2048,
    )

    if stream:
        full = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
        return full.replace("```json", "").replace("```", "").strip()

    raw = response.choices[0].message.content or ""
    return raw.replace("```json", "").replace("```", "").strip()
