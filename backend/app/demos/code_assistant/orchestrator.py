import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from typing import Literal, Optional
from .code_explainer_agent import explain_code
from .code_refactor_agent import refactor_code
from .code_documentation_agent import document_code

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

def orchestrator(user_request: str, code: str, stream: bool = False) -> str:
    """
    Routes user requests to the appropriate specialized agent.
    
    Analyzes the user's request and determines which agent(s) to invoke:
    - explain_code: For understanding what code does
    - refactor_code: For improving code quality and structure
    - document_code: For adding docstrings and comments
    """
    
    # Use LLM to classify the intent and extract parameters
    classification_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": """You are a routing assistant that analyzes user requests about code.
Classify the request into one of these categories:
- "explain": User wants to understand what the code does
- "refactor": User wants to improve code quality, structure, or performance
- "document": User wants to add documentation, docstrings, or comments
- "multiple": User wants multiple operations (e.g., "refactor and document")

Also extract any specific parameters:
- For refactor: extract the refactor_goal if specified (e.g., "improve performance", "reduce complexity")
- For document: extract the doc_style if specified (e.g., "google", "numpy", "sphinx")

Respond in this exact format:
INTENT: [explain|refactor|document|multiple]
OPERATIONS: [comma-separated list if multiple, e.g., "refactor,document"]
REFACTOR_GOAL: [goal if specified, otherwise "none"]
DOC_STYLE: [style if specified, otherwise "google"]"""
            },
            {
                "role": "user",
                "content": f"User request: {user_request}"
            }
        ],
        max_completion_tokens=2048
    )
    
    # Parse the classification response
    classification = classification_response.choices[0].message.content
    lines = classification.strip().split('\n')
    
    intent = None
    operations = []
    refactor_goal = None
    doc_style = "google"
    
    for line in lines:
        if line.startswith("INTENT:"):
            intent = line.split(":", 1)[1].strip().lower()
        elif line.startswith("OPERATIONS:"):
            ops = line.split(":", 1)[1].strip()
            operations = [op.strip() for op in ops.split(",")]
        elif line.startswith("REFACTOR_GOAL:"):
            goal = line.split(":", 1)[1].strip()
            refactor_goal = None if goal.lower() == "none" else goal
        elif line.startswith("DOC_STYLE:"):
            doc_style = line.split(":", 1)[1].strip()
    
    # Route to appropriate agent(s)
    results = []
    
    if intent == "explain":
        print("🔍 Routing to Code Explainer Agent...\n")
        result = explain_code(code, stream=stream)
        results.append(result)
        
    elif intent == "refactor":
        print("🔧 Routing to Code Refactor Agent...\n")
        result = refactor_code(code, refactor_goal=refactor_goal, stream=stream)
        results.append(result)
        
    elif intent == "document":
        print("📝 Routing to Code Documentation Agent...\n")
        result = document_code(code, doc_style=doc_style, stream=stream)
        results.append(result)
        
    elif intent == "multiple":
        print("🔀 Multiple operations detected. Executing in sequence...\n")
        
        for operation in operations:
            operation = operation.lower().strip()
            
            if operation == "explain":
                print("\n🔍 Step 1: Explaining code...\n")
                result = explain_code(code, stream=stream)
                results.append(result)
                
            elif operation == "refactor":
                print("\n🔧 Step 2: Refactoring code...\n")
                result = refactor_code(code, refactor_goal=refactor_goal, stream=stream)
                results.append(result)
                # Update code with refactored version for next step
                if "## Refactored Code" in result:
                    code_section = result.split("## Refactored Code")[1].split("##")[0]
                    code = code_section.strip()
                
            elif operation == "document":
                print("\n📝 Step 3: Adding documentation...\n")
                result = document_code(code, doc_style=doc_style, stream=stream)
                results.append(result)
    
    else:
        # Fallback: default to explanation
        print("Intent unclear. Defaulting to code explanation...\n")
        result = explain_code(code, stream=stream)
        results.append(result)
    
    # Combine results if multiple operations
    if len(results) > 1:
        combined = "\n\n" + "="*80 + "\n\n".join(results)
        return combined
    else:
        return results[0] if results else ""