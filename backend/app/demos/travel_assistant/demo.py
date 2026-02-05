# Demo - Interactive demo to showcase the travel assistant workflow

from app.demos.travel_assistant.orchestrator import run_travel_assistant


def main():
    print("\n")
    print("  Travel Assistant Demo")
    print("=" * 60)
    print("  Get weather and packing advice for your trip!")
    print("  Type 'quit' to exit.\n")

    while True:
        destination = input("Where are you travelling to? → ").strip()

        if destination.lower() in ("quit", "exit", "q"):
            print("\nSafe travels!")
            break

        if not destination:
            print("Please enter a destination.\n")
            continue

        print()
        run_travel_assistant(destination)
        print()


if __name__ == "__main__":
    main()
