# 1st Step.
# Analysis Agent - Gather user's background info
# input - User Conversation(natural language) -> output - structured data
# e.g., education, experience, skills, job preferences

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)


def collect_info(user_input: str, stream: bool = False) -> str:
    """Takes user conversation input and returns structured JSON with resume information."""

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are an expert Resume Information Collector.
Extract user details into a STRICT JSON format.

Output Format (JSON only):
    "name": "string or null",
    "education": ["list of strings"],
    "skills": ["list of strings"],
    "experience": ["list of strings"],
    "projects": ["list of strings"],
    "certifications": ["list of strings"],
    "summary": "brief professional summary string"

Return ONLY the structured summary. Do not add conversational filler."""
            },
            {
                "role": "user",
                "content": f"User Input: {user_input}"
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