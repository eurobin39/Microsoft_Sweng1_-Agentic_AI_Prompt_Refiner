import os
import asyncio
from typing import Any, Optional

from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.azure import AzureOpenAIChatClient

load_dotenv()

_client: Optional[AzureOpenAIChatClient] = None


def _build_client() -> AzureOpenAIChatClient:
    kwargs: dict[str, Any] = {}

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if endpoint:
        kwargs["endpoint"] = endpoint

    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if deployment_name:
        kwargs["deployment_name"] = deployment_name

    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    if api_version:
        kwargs["api_version"] = api_version

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key
        return AzureOpenAIChatClient(**kwargs)

    return AzureOpenAIChatClient(credential=AzureCliCredential(), **kwargs)


def get_client() -> AzureOpenAIChatClient:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def create_agent(*, name: str, instructions: str, tools=None):
    client = get_client()
    return client.as_agent(name=name, instructions=instructions, tools=tools)


def run_agent_sync(agent, prompt: str, **kwargs) -> str:
    async def _run() -> str:
        response = await agent.run(prompt, **kwargs)
        return response.text if hasattr(response, "text") else str(response)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run())
    raise RuntimeError("run_agent_sync cannot be called from a running event loop.")


def run_workflow_sync(workflow, prompt: str):
    async def _run():
        result = await workflow.run(prompt)
        if hasattr(result, "get_outputs"):
            return result.get_outputs()
        return result

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run())
    raise RuntimeError("run_workflow_sync cannot be called from a running event loop.")
