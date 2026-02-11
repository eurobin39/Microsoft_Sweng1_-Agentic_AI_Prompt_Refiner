"""
Legacy compatibility wrapper for travel packing agent.

This module exists to keep older integration tests working after the
Microsoft Agent Framework migration. It provides a simple, direct
function for packing suggestions without requiring LLM setup.
"""

from __future__ import annotations

from .mock_data import mock_packing_list


def get_packing_suggestions(weather_info: str, trip_type: str = "general") -> str:
    """
    Return packing suggestions based on weather info.

    Args:
        weather_info: Weather summary or JSON string.
        trip_type: Trip category (general/business/hiking/beach/city).
    """
    return mock_packing_list(weather_info, trip_type)
