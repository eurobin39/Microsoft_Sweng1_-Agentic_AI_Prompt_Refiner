"""
OpenAI / Azure OpenAI Client
TODO: Implement OpenAI GPT-4 client
"""

from app.services.llm.base import BaseLLM


class OpenAIClient(BaseLLM):
    """OpenAI LLM client implementation"""

    def __init__(self):
        pass

    async def generate(self, prompt: str, **kwargs):
        # TODO: Implement OpenAI API call
        pass
