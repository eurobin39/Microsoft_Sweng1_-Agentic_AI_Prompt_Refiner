# Orchestrator - Runs all agents sequentially

from app.demos.travel_assistant.weather_agent import get_weather
from app.demos.travel_assistant.packing_agent import get_packing_suggestions
from app.demos.travel_assistant.composer_agent import compose_response


def run_travel_assistant(location: str) -> str:
    """
    Runs the full travel assistant workflow:
    1. Weather Agent - gets weather for the location
    2. Packing Agent - suggests items based on weather
    3. Composer Agent - combines into a friendly response
    """
    print("=" * 30)
    print("Travel Assistant Working...")
    print()

    print("\n[1/3] Calling Weather Agent...")
    weather_info = get_weather(location)
    print(f"      Weather: {weather_info}")

    print("\n[2/3] Calling Packing Agent...")
    packing_suggestions = get_packing_suggestions(weather_info)
    print(f"      Packing: {packing_suggestions}")

    print("\n[3/3] Calling Composer Agent...")
    final_response = compose_response(weather_info, packing_suggestions)

    print("\n" )
    print("Final Response:")
    print()
    print(final_response)
    print("=" * 30)

    return final_response


if __name__ == "__main__":
    # Test with a hardcoded location
    run_travel_assistant("Galway, Ireland")
