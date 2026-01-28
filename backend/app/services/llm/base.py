"""
Base LLM Interface
TODO: Define abstract base class for LLM clients
"""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM implementations"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs):
        """Generate a response from the LLM"""
        pass
