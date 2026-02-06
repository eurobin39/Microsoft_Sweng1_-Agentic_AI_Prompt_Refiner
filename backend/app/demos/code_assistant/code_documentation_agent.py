import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

def document_code(code: str, doc_style: str = "google", stream: bool = False) -> str:
    """Takes code as input and returns properly documented version with docstrings and comments."""
    
    # Define documentation style instructions
    style_instructions = {
        "google": "Use Google-style docstrings with Args, Returns, Raises sections",
        "numpy": "Use NumPy-style docstrings with Parameters, Returns, Raises sections",
        "sphinx": "Use Sphinx-style docstrings with :param, :return, :raises tags",
        "pep257": "Use PEP 257 compliant docstrings with simple descriptions"
    }
    
    style_guide = style_instructions.get(doc_style.lower(), style_instructions["google"])
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        stream=stream,
        messages=[
            {
                "role": "system",
                "content": f"""You are a code documentation assistant. When given code:
1. Add comprehensive docstrings to all functions, classes, and modules
2. Add inline comments for complex logic
3. {style_guide}
4. Include type hints where appropriate
5. Document parameters, return values, exceptions, and usage examples
6. Keep comments concise but informative
7. Preserve all original functionality - only add documentation

Format your response as:
## Documented Code
[provide the fully documented code]

## Documentation Summary
[brief summary of what was documented]"""
            },
            {
                "role": "user",
                "content": f"Add documentation to this code:\n\n{code}"
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