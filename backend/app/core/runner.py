import os

from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from app.models.models import AgentBlueprint
from app.models.trace_logs import TraceLog
from .workflow import build_refinement_workflow

load_dotenv()


def get_chat_client() -> AzureOpenAIChatClient:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    if api_key:
        return AzureOpenAIChatClient(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment,
        )
    return AzureOpenAIChatClient(
        credential=AzureCliCredential(),
        endpoint=endpoint,
        deployment_name=deployment,
    )


async def run_evaluation(blueprint: AgentBlueprint, traces: list[TraceLog]):
    # TODO: build workflow, pass blueprint + traces as input, return EvaluationResult
    pass
