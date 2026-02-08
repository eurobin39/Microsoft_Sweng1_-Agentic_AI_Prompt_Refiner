"""
OpenAI / Azure OpenAI Client
"""

import httpx
from typing import Optional
from app.services.llm.base import BaseLLM
from app.config import settings

class OpenAIClient(BaseLLM):
    """Azure OpenAI LLM client implementation using raw HTTPX for stability ///// test then commit"""

    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        # We use a stable, known-working version for Chat Completions
        self.api_version = "2024-08-01-preview"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})

        # Standard Chat Completions URL
        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # FIX: Renamed 'max_tokens' to 'max_completion_tokens' to fix errors.
        payload = {
            "messages": messages,
            "max_completion_tokens": kwargs.get("max_tokens", 2000) 
        }
        

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=60.0)
                
                if response.status_code != 200:
                    print(f"DEBUG: Failed URL: {url}")
                    print(f"DEBUG: Response: {response.text}")
                    raise Exception(f"Azure API Error {response.status_code}: {response.text}")

                data = response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            raise e