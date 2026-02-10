# Packing Agent - Gets weather context, suggests packing items
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv(dotenv_path=".env")

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    api_version="2024-12-01-preview",
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

def get_packing_suggestions(weather_info: str) -> str:
    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": "You are a travel packing assistant. Reply with 6-10 items, comma-separated."
            },
            {
                "role": "user",
                "content": f"Weather: {weather_info}\nPacking items only."
            },
        ],
        max_completion_tokens=256,
    )
    return (resp.choices[0].message.content or "").strip()

if __name__ == "__main__":
    print(get_packing_suggestions("Galway: 11°C, light rain, windy"))
