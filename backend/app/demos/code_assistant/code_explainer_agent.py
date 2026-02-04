import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

def explain_code(code: str) -> str:
    """Takes code as input and returns an explanation."""
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": """You are a code explanation assistant. When given code:
1. Explain what the code does in plain English
2. Break down complex logic step by step
3. Highlight any potential issues or improvements
4. Use clear, beginner-friendly language"""
            },
            {
                "role": "user",
                "content": f"Explain this code:\n\n{code}"
            }
        ],
        max_completion_tokens=2048
    )
    return response.choices[0].message.content