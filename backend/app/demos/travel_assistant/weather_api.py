"""
Real weather data via Open-Meteo API (free, no API key needed).

Replaces mock_weather() and mock_forecast() with live data.
Falls back to mock data if the API call fails (no internet, timeout, etc.).

Usage is identical to the mock versions — same function signatures,
same JSON return format — so agents and tools don't need any changes.

Requires: pip install requests
"""

import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger("travel_assistant")

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT = 8  # seconds


# ─── WMO weather code → human-readable condition ───

_WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _geocode(destination: str) -> tuple[float, float, str] | None:
    """Resolve a place name to (latitude, longitude, resolved_name) via Open-Meteo Geocoding."""
    try:
        resp = requests.get(
            _GEOCODE_URL,
            params={"name": destination, "count": 1, "language": "en", "format": "json"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            r = results[0]
            name = r.get("name", destination)
            country = r.get("country", "")
            label = f"{name}, {country}" if country else name
            return r["latitude"], r["longitude"], label
    except Exception as e:
        logger.warning("Geocoding failed for '%s': %s", destination, e)
    return None


def _estimate_rain_chance(weather_code: int) -> int:
    """Rough rain chance estimate from WMO weather code."""
    if weather_code <= 3:
        return 5
    if weather_code <= 48:
        return 20  # fog
    if weather_code <= 57:
        return 50  # drizzle
    if weather_code <= 67:
        return 75  # rain
    if weather_code <= 77:
        return 60  # snow
    if weather_code <= 82:
        return 80  # rain showers
    if weather_code <= 86:
        return 65  # snow showers
    return 90  # thunderstorm


# ─── Public API (same signatures as mock_data.py) ───

def live_weather(destination: str) -> str:
    """
    Get current weather for a destination using Open-Meteo.
    Returns JSON string matching the mock_weather format.
    Falls back to mock on failure.
    """
    geo = _geocode(destination)
    if not geo:
        logger.info("Geocode miss — falling back to mock for '%s'", destination)
        from .mock_data import mock_weather
        return mock_weather(destination)

    lat, lon, label = geo

    try:
        resp = requests.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})

        temp_c = current.get("temperature_2m", 0)
        weather_code = current.get("weather_code", 0)
        condition = _WMO_CODES.get(weather_code, "Unknown")
        humidity = current.get("relative_humidity_2m", 0)
        wind_kph = current.get("wind_speed_10m", 0)
        rain_chance = _estimate_rain_chance(weather_code)

        return json.dumps({
            "destination": label,
            "current": {
                "temperature_c": temp_c,
                "temperature_f": round(temp_c * 9 / 5 + 32),
                "condition": condition,
                "humidity_pct": humidity,
                "wind_kph": wind_kph,
                "rain_chance_pct": rain_chance,
            },
            "source": "open-meteo.com",
            "retrieved_at": datetime.now().isoformat(),
        }, indent=2)

    except Exception as e:
        logger.warning("Open-Meteo current weather failed: %s — falling back to mock", e)
        from .mock_data import mock_weather
        return mock_weather(destination)


def live_forecast(destination: str, days: int = 5) -> str:
    """
    Get a multi-day forecast for a destination using Open-Meteo.
    Returns JSON string matching the mock_forecast format.
    Falls back to mock on failure.
    """
    geo = _geocode(destination)
    if not geo:
        logger.info("Geocode miss — falling back to mock for '%s'", destination)
        from .mock_data import mock_forecast
        return mock_forecast(destination, days)

    lat, lon, label = geo

    try:
        resp = requests.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": min(days, 16),
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})

        dates = daily.get("time", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        codes = daily.get("weather_code", [])
        rain_probs = daily.get("precipitation_probability_max", [])

        forecast_days = []
        for i in range(min(len(dates), days)):
            code = codes[i] if i < len(codes) else 0
            rain = rain_probs[i] if i < len(rain_probs) else _estimate_rain_chance(code)
            forecast_days.append({
                "date": dates[i],
                "high_c": highs[i] if i < len(highs) else None,
                "low_c": lows[i] if i < len(lows) else None,
                "condition": _WMO_CODES.get(code, "Unknown"),
                "rain_chance_pct": rain,
            })

        return json.dumps({
            "destination": label,
            "forecast": forecast_days,
            "source": "open-meteo.com",
        }, indent=2)

    except Exception as e:
        logger.warning("Open-Meteo forecast failed: %s — falling back to mock", e)
        from .mock_data import mock_forecast
        return mock_forecast(destination, days)