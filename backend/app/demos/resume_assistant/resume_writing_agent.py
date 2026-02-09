# 3rd Step ( BUT VERY IMPORTANT ).
# Resume Writing Agent - Generate Resume Content
# input - structured user background info + key job requirements
# -> output - Resume Text(Markdown or any structured format)

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


def write_resume(user_profile: str, job_analysis: str, stream: bool = False) -> str:
    """Takes user profile data and job analysis, returns a tailored resume in Markdown format."""

    # Initialize client at function level (lazy loading) to handle missing env vars in CI
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-12-01-preview"
    )

    response = client.chat.completions.create(
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
- Do NOT include placeholders like '[Your Name]' if the name is missing; just use generic headers."""
            },
            {
                "role": "user",
                "content": f"User Profile: {user_profile}\n\nJob Analysis Requirements: {job_analysis}"
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
        return full_response
    else:
        print(response.choices[0].message.content)
        return response.choices[0].message.content