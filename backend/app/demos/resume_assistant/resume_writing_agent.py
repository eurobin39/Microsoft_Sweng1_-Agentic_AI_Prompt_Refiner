"""
Legacy compatibility wrapper for Resume Writer.

Provides write_resume(user_profile, job_analysis) without requiring MAF wiring.
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


def write_resume(user_profile: str, job_analysis: str, stream: bool = False) -> str:
    response = _client().chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are an expert Resume Writer.
Write a professional resume in Markdown format.

Instructions:
- Use the 'User Profile' data provided.
- Tailor the content to match the 'Job Analysis' keywords.
- Use professional, action-oriented language.
- Format neatly with Markdown headers (##).
- Do NOT include placeholders like '[Your Name]' if the name is missing; just use generic headers.""",
            },
            {
                "role": "user",
                "content": f"User Profile: {user_profile}\n\nJob Analysis Requirements: {job_analysis}",
            },
        ],
        max_completion_tokens=2048,
    )

    if stream:
        full = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
        return full

    return response.choices[0].message.content or ""
