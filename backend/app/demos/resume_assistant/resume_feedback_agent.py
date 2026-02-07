# 4th Step.
# Feedback Agent - Provide feedback on resume content
# input - generated resume content + job requirements -> output - feedback and suggestions for improvement

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)


def review_resume(resume_content: str, job_analysis: str, stream: bool = False) -> str:
    """Takes generated resume content and job requirements, returns feedback and improvement suggestions."""

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are an expert Resume Reviewer and Career Coach.
Analyze the provided resume against the job requirements and give actionable feedback.

Output Format:
## Overall Score
[X/10 rating with brief justification]

## Strengths
[What the resume does well relative to the job requirements]

## Areas for Improvement
[Specific, actionable suggestions to better align with the role]

## Keyword Gaps
[Important keywords or skills from the job requirements that are missing or underrepresented]

## Rewrite Suggestions
[Concrete rewording suggestions for weak bullet points or sections]

Be specific, constructive, and prioritize changes that would have the most impact on ATS scoring and recruiter appeal."""
            },
            {
                "role": "user",
                "content": f"Resume Content:\n{resume_content}\n\nJob Requirements:\n{job_analysis}"
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