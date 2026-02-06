"""
OpenAI / Azure OpenAI Client
"""



from app.services.llm.base import BaseLLM
from typing import Optional
from openai import AsyncAzureOpenAI
from app.config import settings



class OpenAIClient(BaseLLM):
    """OpenAI LLM client implementation"""

    def __init__(self):
        pass


    # Initialize the Azure client using   from config.py / .env

        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2025-03-01-preview"
        )

        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME




    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str: 
        # ----TODO: Implement OpenAI API call-----
        pass


        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})


        try:

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )

            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            raise e

