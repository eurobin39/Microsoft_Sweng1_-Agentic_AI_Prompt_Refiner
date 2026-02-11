"""
Legacy compatibility wrapper for travel weather agent.

This module exists to keep older integration tests working after the
Microsoft Agent Framework migration. It provides a simple, direct
function that returns weather data without requiring LLM setup.
"""

from __future__ import annotations

from .weather_api import live_weather


def get_weather(destination: str, date: str | None = None) -> str:
    """
    Return current weather for a destination.

    Args:
        destination: City/country name.
        date: Ignored (kept for backward compatibility).
    """
    _ = date
    return live_weather(destination)
