# Weather Agent - Extracts location, calls weather API
# TODO: Implement this agent - it should take a destination and return weather info


def get_weather(destination: str) -> str:
    """
    Takes a travel destination and returns current weather information.

    Should use the Azure OpenAI client to generate or retrieve weather
    information for the given destination.
    """
    return f"{destination}: 14°C, partly cloudy, 40% chance of rain"  # TODO: replace with real implementation
