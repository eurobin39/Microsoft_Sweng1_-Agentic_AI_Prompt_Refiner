"""
Legacy compatibility wrapper for Resume Info Collector.

Provides a direct function (collect_info) without requiring MAF wiring.
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


def collect_info(user_input: str, stream: bool = False) -> str:
    response = _client().chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are an expert Resume Information Collector.
Extract user details into a STRICT JSON format.

Output Format (JSON only):
{
  "name": "string or null",
  "education": ["list of strings"],
  "skills": ["list of strings"],
  "experience": ["list of strings"],
  "projects": ["list of strings"],
  "certifications": ["list of strings"],
  "summary": "brief professional summary string"
}

Return ONLY JSON. Do not add conversational filler. Do not add markdown fences.""",
            },
            {"role": "user", "content": f"User Input: {user_input}"},
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
