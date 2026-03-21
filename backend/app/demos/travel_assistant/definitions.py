"""
Agent definitions for the travel assistant.

Client setup, mock data, weather API, tools, and agent factories — all self-contained.
"""

import json
import logging
import os
import random
import requests
from datetime import datetime, timedelta

from azure.identity import AzureCliCredential
from agent_framework import tool, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

logger = logging.getLogger("travel_assistant")


# ═══════════════════════════ Client ═══════════════════════════

def get_chat_client() -> AzureOpenAIChatClient:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    if api_key:
        return AzureOpenAIChatClient(api_key=api_key, endpoint=endpoint, deployment_name=deployment)
    return AzureOpenAIChatClient(credential=AzureCliCredential(), endpoint=endpoint, deployment_name=deployment)


# ═══════════════════════════ Mock data ═══════════════════════════

def _mock_weather(destination: str) -> str:
    conditions = [
        {"temp_c": 22, "condition": "Sunny", "humidity": 45, "wind_kph": 12, "rain_chance": 5},
        {"temp_c": 14, "condition": "Partly Cloudy", "humidity": 68, "wind_kph": 24, "rain_chance": 40},
        {"temp_c": 8, "condition": "Overcast with Rain", "humidity": 85, "wind_kph": 35, "rain_chance": 80},
        {"temp_c": 30, "condition": "Hot and Humid", "humidity": 78, "wind_kph": 8, "rain_chance": 15},
        {"temp_c": -2, "condition": "Cold and Snowy", "humidity": 70, "wind_kph": 20, "rain_chance": 60},
        {"temp_c": 18, "condition": "Mild and Breezy", "humidity": 55, "wind_kph": 18, "rain_chance": 25},
    ]
    idx = sum(ord(c) for c in destination.lower()) % len(conditions)
    w = conditions[idx]
    return json.dumps({
        "destination": destination,
        "current": {
            "temperature_c": w["temp_c"], "temperature_f": round(w["temp_c"] * 9 / 5 + 32),
            "condition": w["condition"], "humidity_pct": w["humidity"],
            "wind_kph": w["wind_kph"], "rain_chance_pct": w["rain_chance"],
        },
        "retrieved_at": datetime.now().isoformat(),
    }, indent=2)


def _mock_forecast(destination: str, days: int = 5) -> str:
    base_temp = sum(ord(c) for c in destination.lower()) % 25 + 5
    conditions_cycle = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Sunny", "Thunderstorms", "Clear"]
    forecast_days = []
    for i in range(days):
        date = (datetime.now() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        temp_var = random.randint(-3, 3)
        forecast_days.append({
            "date": date, "high_c": base_temp + 4 + temp_var, "low_c": base_temp - 4 + temp_var,
            "condition": conditions_cycle[(sum(ord(c) for c in destination) + i) % len(conditions_cycle)],
            "rain_chance_pct": random.choice([10, 20, 30, 50, 70]),
        })
    return json.dumps({"destination": destination, "forecast": forecast_days}, indent=2)


def _mock_packing_list(weather_summary: str, trip_type: str = "general") -> str:
    base = {
        "essentials": ["Passport/ID", "Phone charger", "Travel adapter", "Toiletries bag"],
        "clothing": ["Underwear (7 days)", "Socks (7 pairs)", "Comfortable walking shoes"],
        "accessories": ["Sunglasses", "Day backpack", "Reusable water bottle"],
    }
    wl = weather_summary.lower()
    if any(w in wl for w in ["rain", "cloudy", "overcast"]):
        base["clothing"].extend(["Waterproof jacket", "Umbrella"])
    if any(w in wl for w in ["cold", "snow"]):
        base["clothing"].extend(["Warm coat", "Gloves", "Beanie", "Scarf"])
    if any(w in wl for w in ["hot", "sunny", "humid"]):
        base["clothing"].extend(["Light breathable shirts", "Shorts", "Sun hat", "Sunscreen SPF50"])
    if any(w in wl for w in ["mild", "breezy", "partly"]):
        base["clothing"].extend(["Light jacket", "Long-sleeve shirts"])
    extras = {
        "business": ["Formal shirt/blouse", "Dress shoes", "Laptop + charger"],
        "hiking": ["Hiking boots", "Trekking poles", "First aid kit"],
        "beach": ["Swimsuit", "Flip flops", "Beach towel"],
        "city": ["Smart casual outfit", "Camera", "Portable battery"],
        "general": ["Versatile outfit layers", "Camera"],
    }
    base["trip_specific"] = extras.get(trip_type.lower(), extras["general"])
    return json.dumps({"packing_list": base, "trip_type": trip_type}, indent=2)


def _mock_activities(destination: str, category: str = "all") -> str:
    db = {
        "sightseeing": [
            {"name": f"Walking Tour of {destination}", "duration": "3h", "price_usd": 25, "rating": 4.7},
            {"name": f"{destination} Historical Museum", "duration": "2h", "price_usd": 15, "rating": 4.5},
        ],
        "food": [
            {"name": f"Local Food Tour in {destination}", "duration": "3.5h", "price_usd": 65, "rating": 4.9},
            {"name": "Street Food Market Visit", "duration": "2h", "price_usd": 0, "rating": 4.4},
        ],
        "outdoor": [
            {"name": f"Day Hike near {destination}", "duration": "5h", "price_usd": 40, "rating": 4.7},
            {"name": "Bike Tour", "duration": "3h", "price_usd": 35, "rating": 4.5},
        ],
        "culture": [
            {"name": "Live Music / Theatre", "duration": "2.5h", "price_usd": 45, "rating": 4.6},
            {"name": "Art Gallery Crawl", "duration": "3h", "price_usd": 20, "rating": 4.4},
        ],
    }
    selected = db if category.lower() == "all" else {category: db.get(category.lower(), db["sightseeing"])}
    return json.dumps({"destination": destination, "activities": selected}, indent=2)


def _mock_local_tips(destination: str) -> str:
    return json.dumps({
        "destination": destination,
        "tips": {
            "currency": "Check XE.com for current rates",
            "tipping": "10-15% at restaurants is standard in most countries",
            "safety": "Generally safe for tourists. Keep valuables secure in crowded areas.",
            "transport": f"Public transport in {destination} is recommended.",
        },
    }, indent=2)


def _mock_search_flights(origin: str, destination: str, date: str = "2025-03-01") -> str:
    airlines = ["Aer Lingus", "Ryanair", "Lufthansa", "KLM", "Emirates", "British Airways"]
    base_price = (sum(ord(c) for c in destination) % 400) + 150
    flights = []
    for i in range(4):
        dep_h = 6 + (i * 4)
        dur = 2 + (sum(ord(c) for c in destination) % 10)
        flights.append({
            "flight_id": f"FL-{1000 + i}",
            "airline": airlines[(sum(ord(c) for c in destination) + i) % len(airlines)],
            "departure": f"{date}T{dep_h:02d}:00:00",
            "duration_hours": dur, "stops": 0 if i < 2 else 1,
            "price_eur": base_price + (i * 45) + random.randint(-20, 40),
        })
    return json.dumps({"origin": origin, "destination": destination, "flights": flights}, indent=2)


def _mock_search_hotels(destination: str, checkin: str = "2025-03-01", nights: int = 3) -> str:
    names = [f"Grand Hotel {destination}", f"The {destination} Inn", f"Budget Stay {destination}"]
    base_price = (sum(ord(c) for c in destination) % 80) + 60
    hotels = []
    for i, name in enumerate(names):
        price = base_price + (i * 30) + random.randint(-10, 20)
        hotels.append({
            "hotel_id": f"HTL-{2000 + i}", "name": name, "stars": min(5, 2 + i),
            "price_per_night_eur": price, "total_eur": price * nights,
        })
    return json.dumps({"destination": destination, "checkin": checkin, "nights": nights, "hotels": hotels}, indent=2)


# ═══════════════════════════ Weather API (with mock fallback) ═══════════════════════════

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain",
    65: "Heavy rain", 71: "Slight snowfall", 80: "Slight rain showers", 95: "Thunderstorm",
}


def _geocode(destination: str) -> tuple[float, float, str] | None:
    try:
        resp = requests.get(
            _GEOCODE_URL,
            params={"name": destination, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            r = results[0]
            label = f"{r.get('name', destination)}, {r.get('country', '')}".strip(", ")
            return r["latitude"], r["longitude"], label
    except Exception as e:
        logger.warning("Geocoding failed for '%s': %s", destination, e)
    return None


def _live_weather(destination: str) -> str:
    geo = _geocode(destination)
    if not geo:
        return _mock_weather(destination)
    lat, lon, label = geo
    try:
        resp = requests.get(
            _FORECAST_URL,
            params={"latitude": lat, "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "timezone": "auto"},
            timeout=8,
        )
        resp.raise_for_status()
        current = resp.json().get("current", {})
        temp_c = current.get("temperature_2m", 0)
        code = current.get("weather_code", 0)
        return json.dumps({
            "destination": label,
            "current": {
                "temperature_c": temp_c, "temperature_f": round(temp_c * 9 / 5 + 32),
                "condition": _WMO_CODES.get(code, "Unknown"),
                "humidity_pct": current.get("relative_humidity_2m", 0),
                "wind_kph": current.get("wind_speed_10m", 0),
            },
            "source": "open-meteo.com",
        }, indent=2)
    except Exception as e:
        logger.warning("Weather API failed: %s — falling back to mock", e)
        return _mock_weather(destination)


def _live_forecast(destination: str, days: int = 5) -> str:
    geo = _geocode(destination)
    if not geo:
        return _mock_forecast(destination, days)
    lat, lon, label = geo
    try:
        resp = requests.get(
            _FORECAST_URL,
            params={"latitude": lat, "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
                    "timezone": "auto", "forecast_days": min(days, 16)},
            timeout=8,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        dates = daily.get("time", [])
        forecast_days = []
        for i in range(min(len(dates), days)):
            code = daily.get("weather_code", [0] * (i + 1))[i]
            forecast_days.append({
                "date": dates[i],
                "high_c": daily.get("temperature_2m_max", [None] * (i + 1))[i],
                "low_c": daily.get("temperature_2m_min", [None] * (i + 1))[i],
                "condition": _WMO_CODES.get(code, "Unknown"),
                "rain_chance_pct": daily.get("precipitation_probability_max", [0] * (i + 1))[i],
            })
        return json.dumps({"destination": label, "forecast": forecast_days, "source": "open-meteo.com"}, indent=2)
    except Exception as e:
        logger.warning("Forecast API failed: %s — falling back to mock", e)
        return _mock_forecast(destination, days)


# ═══════════════════════════ Tools ═══════════════════════════

@tool(name="get_weather", description="Get current weather for a destination.")
def get_weather(destination: str) -> str:
    return _live_weather(destination)


@tool(name="get_forecast", description="Get a multi-day weather forecast for a destination.")
def get_forecast(destination: str, days: int = 5) -> str:
    return _live_forecast(destination, days)


@tool(name="get_packing_list", description="Generate a packing list based on weather and trip type.")
def get_packing_list(weather_summary: str, trip_type: str = "general") -> str:
    return _mock_packing_list(weather_summary, trip_type)


@tool(name="get_activities", description="Get activity suggestions for a destination.")
def get_activities(destination: str, category: str = "all") -> str:
    return _mock_activities(destination, category)


@tool(name="get_local_tips", description="Get local tips for a destination.")
def get_local_tips(destination: str) -> str:
    return _mock_local_tips(destination)


@tool(name="search_flights", description="Search for available flights between two cities.")
def search_flights(origin: str, destination: str, date: str = "2025-03-01") -> str:
    return _mock_search_flights(origin, destination, date)


@tool(name="search_hotels", description="Search for available hotels at a destination.")
def search_hotels(destination: str, checkin: str = "2025-03-01", nights: int = 3) -> str:
    return _mock_search_hotels(destination, checkin, nights)


# ═══════════════════════════ Agent Factories ═══════════════════════════

def create_triage_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="triage_agent",
        instructions="Route the user to the right agent.",
        chat_client=chat_client,
    )


def create_weather_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="weather_agent",
        instructions="Tell the user about the weather.",
        chat_client=chat_client,
        tools=[get_weather, get_forecast],
    )


def create_packing_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="packing_agent",
        instructions="Help the user figure out what to pack.",
        chat_client=chat_client,
        tools=[get_packing_list],
    )


def create_activities_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="activities_agent",
        instructions="Suggest things to do at the destination.",
        chat_client=chat_client,
        tools=[get_activities, get_local_tips],
    )


def create_booking_agent(chat_client: AzureOpenAIChatClient) -> ChatAgent:
    return ChatAgent(
        name="booking_agent",
        instructions="Help the user find flights and hotels.",
        chat_client=chat_client,
        tools=[search_flights, search_hotels],
    )
