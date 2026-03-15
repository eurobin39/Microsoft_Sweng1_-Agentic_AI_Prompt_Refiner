import os

from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv


from app.models.models import AgentBlueprint, EvaluationResult
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


async def run_evaluation(blueprint: AgentBlueprint, traces: list[TraceLog]) -> EvaluationResult:
    # 1. Get client and build workflow
    chat_client = get_chat_client()
    workflow = build_refinement_workflow(chat_client)
    
    # 2. Serialize inputs to dicts for the workflow payload
    payload = {
        "blueprint": blueprint.model_dump(),
        "traces": [trace.model_dump() for trace in traces]
    }
    
    # 3. Invoke the workflow and await the result
    result = await workflow.invoke(payload)
    
    # 4. Parse the raw dictionary back into an EvaluationResult
    return EvaluationResult(**result)