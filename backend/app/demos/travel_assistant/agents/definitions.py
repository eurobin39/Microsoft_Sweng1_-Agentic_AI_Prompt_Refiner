"""
Agent definitions for the travel assistant.

Each agent is created via chat_client.as_agent() following the official MAF pattern.
Tools use the @ai_function decorator for automatic schema inference.

Agents:
  - TriageAgent: classifies intent, hands off to specialists
  - WeatherAgent: current weather and forecasts
  - PackingAgent: packing lists and luggage tips
  - ActivitiesAgent: things to do and local tips
  - BookingAgent: flight/hotel search and booking
"""

from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from ..mock_data import (
    mock_packing_list, mock_luggage_restrictions,
    mock_activities, mock_local_tips,
    mock_search_flights, mock_search_hotels, mock_book_flight, mock_book_hotel,
)
from ..weather_api import live_weather, live_forecast


# ═══════════════════════════ Tools ═══════════════════════════

# ── Weather tools ──
@tool(name="get_weather", description="Get current weather conditions for a travel destination.")
def get_weather(destination: str) -> str:
    return live_weather(destination)

@tool(name="get_forecast", description="Get a multi-day weather forecast for a travel destination.")
def get_forecast(destination: str, days: int = 5) -> str:
    return live_forecast(destination, days)

# ── Packing tools ──
@tool(name="get_packing_list", description="Generate a packing list based on weather conditions and trip type (general/business/hiking/beach/city).")
def get_packing_list(weather_summary: str, trip_type: str = "general") -> str:
    return mock_packing_list(weather_summary, trip_type)

@tool(name="check_luggage_restrictions", description="Check airline luggage restrictions, weight limits, and prohibited items.")
def check_luggage_restrictions(airline: str = "general") -> str:
    return mock_luggage_restrictions(airline)

# ── Activities tools ──
@tool(name="get_activities", description="Get activity suggestions for a destination. Category: all/sightseeing/food/outdoor/culture.")
def get_activities(destination: str, category: str = "all") -> str:
    return mock_activities(destination, category)

@tool(name="get_local_tips", description="Get local tips: currency, language basics, safety, and transport for a destination.")
def get_local_tips(destination: str) -> str:
    return mock_local_tips(destination)

# ── Booking tools ──
@tool(name="search_flights", description="Search for available flights from origin to destination on a given date.")
def search_flights(origin: str, destination: str, date: str = "2025-03-01") -> str:
    return mock_search_flights(origin, destination, date)

@tool(name="search_hotels", description="Search for available hotels at a destination for a check-in date and number of nights.")
def search_hotels(destination: str, checkin: str = "2025-03-01", nights: int = 3) -> str:
    return mock_search_hotels(destination, checkin, nights)

@tool(name="book_flight", description="Book a specific flight by flight ID for a passenger.")
def book_flight(flight_id: str, passenger_name: str) -> str:
    return mock_book_flight(flight_id, passenger_name)

@tool(name="book_hotel", description="Book a specific hotel by hotel ID for a guest.")
def book_hotel(hotel_id: str, guest_name: str, nights: int = 3) -> str:
    return mock_book_hotel(hotel_id, guest_name, nights)


# ═══════════════════════════ Agent Factories ═══════════════════════════

def create_triage_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    """
    Triage agent — used as the start agent in HandoffBuilder.

    The handoff tools (handoff_to_weather_agent, handoff_to_booking_agent, etc.)
    are automatically registered by HandoffBuilder. The instructions tell the
    agent when to use each one.
    """
    return ChatAgent(
        name="triage_agent",
        instructions=(
            "You are a travel assistant triage agent. Analyse the user's request and "
            "route it to the appropriate specialist:\n\n"
            "- For weather questions → call handoff_to_weather_agent\n"
            "- For packing/luggage questions → call handoff_to_packing_agent\n"
            "- For activity/sightseeing questions → call handoff_to_activities_agent\n"
            "- For flight/hotel/booking questions → call handoff_to_booking_agent\n\n"
            "If the request covers multiple topics, pick the most relevant specialist first. "
            "The specialist can hand off to another if needed.\n"
            "Be friendly and brief when responding directly."
        ),
        chat_client=chat_client,
    )


def create_weather_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="weather_agent",
        instructions=(
            "You are a travel weather specialist. Use get_weather for current conditions "
            "and get_forecast for multi-day outlooks. Summarise clearly: temperature, "
            "conditions, rain chance. Highlight notable day-to-day changes in forecasts. "
            "If the user also needs packing advice, call handoff_to_packing_agent. "
            "If they need activities, call handoff_to_activities_agent."
        ),
        chat_client=chat_client,
        tools=[get_weather, get_forecast],
    )


def create_packing_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="packing_agent",
        instructions=(
            "You are a travel packing specialist. Use the conversation's weather context "
            "to call get_packing_list with an appropriate trip_type. Also offer luggage tips "
            "via check_luggage_restrictions. Organise suggestions by category. Be concise."
        ),
        chat_client=chat_client,
        tools=[get_packing_list, check_luggage_restrictions],
    )


def create_activities_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="activities_agent",
        instructions=(
            "You are a local travel guide. Use get_activities for destination suggestions "
            "and get_local_tips for practical advice. Highlight top-rated options and hidden "
            "gems. Tailor to weather if context is available. Be enthusiastic but concise."
        ),
        chat_client=chat_client,
        tools=[get_activities, get_local_tips],
    )


def create_booking_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="booking_agent",
        instructions=(
            "You are a travel booking specialist. Use search_flights and search_hotels to "
            "show options with prices and ratings. Highlight best value and premium options. "
            "When asked to book, use book_flight or book_hotel and confirm the reference. "
            "Always confirm details before booking."
        ),
        chat_client=chat_client,
        tools=[search_flights, search_hotels, book_flight, book_hotel],
    )