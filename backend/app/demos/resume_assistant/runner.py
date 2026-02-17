"""
Resume Assistant — MAF runner.

Provides a robust interface for running the sequential workflow.
Successfully extracts text from MAF Beta's WorkflowEvent streams.
"""

import os
import asyncio
from typing import Any, Dict

from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from .workflows.sequential import build_sequential_workflow

load_dotenv()

def get_chat_client() -> AzureOpenAIChatClient:
    """Create an AzureOpenAIChatClient with hardcoded fallback credentials."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or "https://ai-hub-tcd.cognitiveservices.azure.com/"
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or "F4uBZXKF3LQJemRKKwMfh0KvAMLlahNv6s6IeJd57PcyE81TstFlJQQJ99CBACfhMk5XJ3w3AAAAACOGystX"
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.2-chat"

    if api_key:
        return AzureOpenAIChatClient(
            api_key=api_key, 
            endpoint=endpoint, 
            deployment_name=deployment
        )
    return AzureOpenAIChatClient(
        credential=AzureCliCredential(), 
        endpoint=endpoint, 
        deployment_name=deployment
    )

async def run_workflow(
    user_request: str, 
    stream: bool = True,
    mode: str = "sequential",
    log_file: str | None = None,
    trace_dir: str = "resume_assistant/log/traces"
) -> Dict[str, Any]:
    """Run the workflow and extract the generated text from WorkflowEvents."""
    chat_client = get_chat_client()
    workflow = build_sequential_workflow(chat_client)

    print("\n⏳ The AI Agents are currently working on your request... Please wait...\n")
    
    # Execute the workflow
    execution_result = await workflow.run(user_request)
    
    final_output = ""
    agents_trace = {}

    try:
        # Parse the WorkflowEvent list returned by the MAF Beta framework
        if isinstance(execution_result, list):
            for event in execution_result:
                event_type = getattr(event, "type", "")
                executor = getattr(event, "executor_id", "Agent")
                
                # Extract only when an agent finishes its task
                if event_type == "executor_completed":
                    data = getattr(event, "data", [])
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        # Step into AgentExecutorResponse if wrapped
                        if hasattr(item, "agent_response"):
                            item = item.agent_response
                            
                        # Extract text from AgentResponse
                        text = getattr(item, "text", "")
                        if not text and hasattr(item, "messages"):
                            msgs = item.messages
                            if isinstance(msgs, list) and msgs:
                                last_msg = msgs[-1]
                                text = getattr(last_msg, "content", getattr(last_msg, "text", ""))
                        
                        # Deduplicate and format the output
                        if text and text.strip() and executor not in agents_trace:
                            agents_trace[executor] = {"output": text.strip()}
                            final_output += f"\n========================================\n🤖 [{executor}]:\n{text.strip()}\n"
        
        if not final_output.strip():
            final_output = "⚠️ [DEBUG] Extraction failed. No text found in completed events."
            
    except Exception as e:
        final_output = f"⚠️ [DEBUG] Extraction Error: {e}"

    print(final_output)

    return {
        "final_output": final_output, 
        "agents": agents_trace
    }

def run_sync(
    user_request: str, 
    stream: bool = True,
    mode: str = "sequential",
    log_file: str | None = None,
    trace_dir: str = "resume_assistant/log/traces"
) -> Dict[str, Any]:
    """Synchronous wrapper matching the demo's required signature."""
    return asyncio.run(run_workflow(
        user_request, 
        stream=stream, 
        mode=mode, 
        log_file=log_file, 
        trace_dir=trace_dir
    ))