# Composer Agent - Combines agent outputs into final response

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    api_version="2024-12-01-preview"
)


def compose_response(weather_info: str, packing_suggestions: str) -> str:
    """
    Takes weather information and packing suggestions from other agents and forms a cohesive response.
    """
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
        messages=[
            {
                "role": "system",
                "content": """You are a friendly travel assistant composing final responses.

Given weather information and packing suggestions from other sources, create a single
conversational response that:
1. Sounds natural and helpful, like a knowledgeable friend
2. Smoothly combines the weather and packing info (don't just list them separately)
3. Keeps it concise - 3-4 sentences max
4. Adds a friendly touch without being over the top"""
            },
            {
                "role": "user",
                "content": f"""Combine this into a friendly response for the traveller:

Weather Information:
{weather_info}

Packing Suggestions:
{packing_suggestions}"""
            }
        ],
        max_completion_tokens=512
    )

    return response.choices[0].message.content or ""


if __name__ == "__main__":
    # Test with sample data
    test_weather = "Galway, Ireland: 12°C, 60% chance of rain, windy conditions expected"
    test_packing = "Waterproof jacket, layers, water-resistant shoes, umbrella, warm sweater"

    print("Testing Composer Agent")
    print("=" * 50)
    result = compose_response(test_weather, test_packing)
    print(result)
