import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

def refactor_code(code: str, refactor_goal: str = None, stream: bool = False) -> str:
    """Takes code as input and returns refactored version with improvements."""
    
    # Build the user prompt based on whether a specific goal is provided
    if refactor_goal:
        user_prompt = f"Refactor this code with focus on: {refactor_goal}\n\n{code}"
    else:
        user_prompt = f"Refactor this code:\n\n{code}"
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": """You are a code refactoring assistant. When given code:
1. Identify code smells and areas for improvement
2. Suggest refactored code with better structure, readability, and maintainability
3. Explain what changes you made and why
4. Follow best practices and design patterns
5. Preserve the original functionality while improving code quality

Format your response as:
## Refactored Code
[provide the improved code]

## Changes Made
[explain the improvements]

## Reasoning
[explain why these changes improve the code]"""
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        max_completion_tokens=2048
    )
    
    if stream:
        # Streaming: print chunks as they arrive, collect full response
        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()  # Newline at the end
        return full_response
    else:
        # Non-streaming: return complete response
        print(response.choices[0].message.content)
        return response.choices[0].message.content
