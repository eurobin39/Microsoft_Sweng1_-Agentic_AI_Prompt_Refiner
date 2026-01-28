"""
Mistral AI Client
TODO: Implement Mistral API client
"""

from app.services.llm.base import BaseLLM


class MistralClient(BaseLLM):
    """Mistral LLM client implementation"""

    def __init__(self):
        pass

    async def generate(self, prompt: str, **kwargs):
        # TODO: Implement Mistral API call
        pass
