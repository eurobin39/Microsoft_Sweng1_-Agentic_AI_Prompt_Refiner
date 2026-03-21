import json
from typing import Dict

from agent_framework import (
    AgentResponseUpdate,
    AgentRunUpdateEvent,
    ChatAgent,
    ExecutorCompletedEvent,
    ExecutorInvokedEvent,
    WorkflowBuilder,
)

from app.core.runner import get_chat_client

EXTRACTION_SYSTEM_PROMPT = """\
You are analysing a GitHub repository to produce an AgentBlueprint JSON object.

The AgentBlueprint schema:
{
  "agent": {
    "name": string | null,
    "description": string | null,
    "system_prompt": string,        // REQUIRED — infer from code or README if not explicit
    "model": string | null,
    "provider": "azure_openai" | "openai" | "anthropic" | "mistral" | "grok" | null,
    "model_parameters": {
      "temperature": float | null,
      "max_tokens": int | null,
      "top_p": float | null
    } | null,
    "tools": [
      { "name": string, "description": string, "parameters": object | null }
    ],
    "output_format": "text" | "json" | "markdown" | null,
    "output_schema": object | null
  },
  "test_cases": [                   // REQUIRED — at least one entry
    {
      "description": string | null,
      "input": string,              // REQUIRED
      "expected_output": string | null,
      "expected_behavior": string | null,
      "context": object | null
    }
  ],
  "evaluation_criteria": {
    "goals": [string],
    "constraints": [string],
    "priority_description": string | null
  } | null
}

Rules:
- system_prompt is always required. If not found verbatim, synthesise one from the agent's purpose.
- test_cases must contain at least one entry. Derive from README examples, usage snippets, or the agent's purpose.
- Detect provider from imports: openai/azure → openai or azure_openai, anthropic → anthropic.
- Extract tool definitions from @tool decorators, function signatures, or schema objects.
- Omit unknown fields — stick strictly to the schema above.
- Return ONLY valid JSON. No markdown fences, no explanation.
"""


def _build_files_text(file_contents: Dict[str, str]) -> str:
    return "\n\n".join(
        f"=== {path} ===\n{content}" for path, content in file_contents.items()
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    return text


async def extract_blueprint(file_contents: Dict[str, str]) -> dict:
    """Extract an AgentBlueprint dict from repo file contents using the agent framework."""
    chat_client = get_chat_client()

    agent = ChatAgent(
        name="extractor_agent",
        instructions=EXTRACTION_SYSTEM_PROMPT,
        chat_client=chat_client,
        tools=[],
    )

    workflow = WorkflowBuilder().set_start_executor(agent).build()

    files_text = _build_files_text(file_contents)
    message = f"Extract the AgentBlueprint JSON from these repository files:\n\n{files_text}"

    _buffers: dict[str, list[str]] = {}
    _current_agent: str | None = None
    _last_text: str = ""

    async for event in workflow.run_stream(message):
        if isinstance(event, ExecutorInvokedEvent):
            _current_agent = event.executor_id
            if _current_agent:
                _buffers[_current_agent] = []

        elif isinstance(event, AgentRunUpdateEvent):
            executor_id = event.executor_id or _current_agent
            data = event.data
            if isinstance(data, AgentResponseUpdate):
                text = getattr(data, "text", "") or ""
                if text and executor_id:
                    _buffers.setdefault(executor_id, []).append(text)

        elif isinstance(event, ExecutorCompletedEvent):
            executor_id = event.executor_id
            if executor_id and executor_id in _buffers:
                text = "".join(_buffers.pop(executor_id))
                if text.strip():
                    _last_text = text

    if not _last_text:
        raise RuntimeError("Extractor agent returned no output")

    return json.loads(_strip_fences(_last_text))
