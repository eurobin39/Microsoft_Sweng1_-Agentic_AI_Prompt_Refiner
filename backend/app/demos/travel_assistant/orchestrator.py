# Orchestrator - Routes user requests to the appropriate travel agent(s)
#Testing CICD pipeline

import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from .travel_weather_agent import get_weather
from .travel_packing_agent import get_packing_suggestions

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    api_version="2024-12-01-preview"
)


def orchestrator(user_request: str, stream: bool = False) -> str:
    """
    Routes user requests to the appropriate specialized travel agent.

    Analyzes the user's request and determines which agent(s) to invoke:
    - get_weather: For weather information about a destination
    - get_packing_suggestions: For packing advice
    - both: For full trip advice (weather + packing composed into a friendly response)
    """

    # Use LLM to classify the intent and extract parameters
    classification_response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT",""),
        messages=[
            {
                "role": "system",
                "content": """You are a routing assistant that analyzes user requests about travel.
Classify the request into one of these categories:
- "weather": User only wants weather information for a destination
- "packing": User only wants packing suggestions for a destination
- "both": User wants full trip advice (weather AND packing combined into a friendly response)

Also extract the travel destination from the request.

Also extract the travel date from the request. If no date is mentioned, use today's date.

Respond in this exact format:
INTENT: [weather|packing|both]
DESTINATION: [extracted destination, e.g. "Paris, France"]
DATE: [extracted date in YYYY-MM-DD format]"""
            },
            {
                "role": "user",
                "content": f"User request: {user_request}"
            }
        ],
        max_completion_tokens=200
    )

    # Parse the classification response
    classification = classification_response.choices[0].message.content or ""
    lines = classification.strip().split('\n')

    intent = None
    destination = None
    date = None

    for line in lines:
        if line.startswith("INTENT:"):
            intent = line.split(":", 1)[1].strip().lower()
        elif line.startswith("DESTINATION:"):
            destination = line.split(":", 1)[1].strip()
        elif line.startswith("DATE:"):
            date = line.split(":", 1)[1].strip()

    if not destination:
        return "Sorry, I couldn't work out a destination from your request. Could you try again?"

    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

    # Route to appropriate agent(s)
    if intent == "weather":
        print("Routing to Weather Agent...\n")
        return get_weather(destination, date)

    elif intent == "packing":
        print("Routing to Packing Agent...\n")
        # Packing agent needs weather context, so call weather first
        weather_info = get_weather(destination, date)
        return get_packing_suggestions(weather_info)

    elif intent == "both":
        print("Multiple agents needed. Executing in sequence...\n")

        print("[1/2] Calling Weather Agent...")
        weather_info = get_weather(destination, date)
        print(f"      Weather: {weather_info}")

        print("\n[2/2] Calling Packing Agent...")
        packing_suggestions = get_packing_suggestions(weather_info)
        print(f"      Packing: {packing_suggestions}")

        # Compose a final friendly response from both agent outputs
        print("\nComposing final response...")
        return _compose_final_response(weather_info, packing_suggestions)

    else:
        # Fallback: default to full trip advice
        print("Intent unclear. Defaulting to full trip advice...\n")
        weather_info = get_weather(destination, date)
        packing_suggestions = get_packing_suggestions(weather_info)
        return _compose_final_response(weather_info, packing_suggestions)


def _compose_final_response(weather_info: str, packing_suggestions: str) -> str:
    """
    Composes weather and packing info into a single friendly response.
    Called by the orchestrator when both agents have been invoked.
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
