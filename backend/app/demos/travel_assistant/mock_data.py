"""
Mock data for travel assistant tools.

Each function returns realistic, structured data that mimics what a real API would return.
To swap in real APIs later, replace the function bodies — signatures stay the same.
"""

import json
import random
from datetime import datetime, timedelta


# ─────────────────────────── Weather ───────────────────────────

def mock_weather(destination: str) -> str:
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


def mock_forecast(destination: str, days: int = 5) -> str:
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


# ─────────────────────────── Packing ───────────────────────────

def mock_packing_list(weather_summary: str, trip_type: str = "general") -> str:
    base = {
        "essentials": ["Passport/ID", "Phone charger", "Travel adapter", "Toiletries bag", "Medications"],
        "clothing": ["Underwear (7 days)", "Socks (7 pairs)", "Comfortable walking shoes"],
        "accessories": ["Sunglasses", "Day backpack", "Reusable water bottle"],
    }
    wl = weather_summary.lower()
    if any(w in wl for w in ["rain", "cloudy", "overcast"]):
        base["clothing"].extend(["Waterproof jacket", "Umbrella", "Quick-dry trousers"])
    if any(w in wl for w in ["cold", "snow", "-"]):
        base["clothing"].extend(["Warm coat", "Thermal layers", "Gloves", "Beanie", "Scarf"])
    if any(w in wl for w in ["hot", "sunny", "humid"]):
        base["clothing"].extend(["Light breathable shirts", "Shorts", "Sun hat", "Sunscreen SPF50"])
    if any(w in wl for w in ["mild", "breezy", "partly"]):
        base["clothing"].extend(["Light jacket", "Layers", "Long-sleeve shirts"])
    extras = {
        "business": ["Formal shirt/blouse", "Dress shoes", "Laptop + charger", "Blazer"],
        "hiking": ["Hiking boots", "Trekking poles", "Trail snacks", "First aid kit", "Headlamp"],
        "beach": ["Swimsuit", "Flip flops", "Beach towel", "Reef-safe sunscreen"],
        "city": ["City map/guidebook", "Smart casual outfit", "Camera", "Portable battery"],
        "general": ["Versatile outfit layers", "Comfortable shoes", "Camera"],
    }
    base["trip_specific"] = extras.get(trip_type.lower(), extras["general"])
    return json.dumps({"packing_list": base, "trip_type": trip_type, "total_items": sum(len(v) for v in base.values())}, indent=2)


def mock_luggage_restrictions(airline: str = "general") -> str:
    return json.dumps({
        "airline": airline,
        "carry_on": {"max_weight_kg": 7, "max_dimensions_cm": "55 x 40 x 20"},
        "checked": {"max_weight_kg": 23, "max_dimensions_cm": "158 linear cm", "free_bags": 1},
        "prohibited_items": ["Liquids over 100ml in carry-on", "Sharp objects in carry-on", "Lithium batteries in checked luggage"],
        "tips": ["Pack liquids in a clear resealable bag", "Wear heaviest shoes on the plane", "Roll clothes to save space"],
    }, indent=2)


# ─────────────────────────── Activities ───────────────────────────

def mock_activities(destination: str, category: str = "all") -> str:
    db = {
        "sightseeing": [
            {"name": f"Walking Tour of {destination}", "duration": "3h", "price_usd": 25, "rating": 4.7},
            {"name": f"{destination} Historical Museum", "duration": "2h", "price_usd": 15, "rating": 4.5},
            {"name": "Panoramic City View Point", "duration": "1h", "price_usd": 0, "rating": 4.8},
        ],
        "food": [
            {"name": f"Local Food Tour in {destination}", "duration": "3.5h", "price_usd": 65, "rating": 4.9},
            {"name": "Cooking Class - Local Cuisine", "duration": "4h", "price_usd": 80, "rating": 4.6},
            {"name": "Street Food Market Visit", "duration": "2h", "price_usd": 0, "rating": 4.4},
        ],
        "outdoor": [
            {"name": f"Day Hike near {destination}", "duration": "5h", "price_usd": 40, "rating": 4.7},
            {"name": "Bike Tour", "duration": "3h", "price_usd": 35, "rating": 4.5},
            {"name": "Kayaking / Water Sports", "duration": "2h", "price_usd": 55, "rating": 4.3},
        ],
        "culture": [
            {"name": "Live Music / Theatre", "duration": "2.5h", "price_usd": 45, "rating": 4.6},
            {"name": "Art Gallery Crawl", "duration": "3h", "price_usd": 20, "rating": 4.4},
            {"name": "Local Market & Artisan Shops", "duration": "2h", "price_usd": 0, "rating": 4.5},
        ],
    }
    selected = db if category.lower() == "all" else {category: db.get(category.lower(), db["sightseeing"])}
    return json.dumps({"destination": destination, "activities": selected, "total_options": sum(len(v) for v in selected.values())}, indent=2)


def mock_local_tips(destination: str) -> str:
    return json.dumps({
        "destination": destination,
        "tips": {
            "currency": "Check XE.com for current rates",
            "language_basics": ["Hello", "Thank you", "Excuse me", "How much?"],
            "tipping": "10-15% at restaurants is standard in most countries",
            "safety": f"Generally safe for tourists. Keep valuables secure in crowded areas.",
            "transport": f"Public transport in {destination} is recommended. Consider a day pass.",
        },
    }, indent=2)


# ─────────────────────────── Flights & Hotels ───────────────────────────

def mock_search_flights(origin: str, destination: str, date: str = "2025-03-01") -> str:
    airlines = ["Aer Lingus", "Ryanair", "Lufthansa", "KLM", "Emirates", "British Airways"]
    base_price = (sum(ord(c) for c in destination) % 400) + 150
    flights = []
    for i in range(4):
        airline = airlines[(sum(ord(c) for c in destination) + i) % len(airlines)]
        dep_h = 6 + (i * 4)
        dur = 2 + (sum(ord(c) for c in destination) % 10)
        stops = 0 if i < 2 else 1
        flights.append({
            "flight_id": f"FL-{1000 + i}", "airline": airline,
            "departure": f"{date}T{dep_h:02d}:{'00' if i % 2 == 0 else '30'}:00",
            "duration_hours": dur + (0.5 if stops else 0), "stops": stops,
            "price_eur": base_price + (i * 45) + random.randint(-20, 40),
            "cabin_class": "Economy", "seats_remaining": random.randint(2, 45),
        })
    return json.dumps({"origin": origin, "destination": destination, "date": date, "flights": flights}, indent=2)


def mock_search_hotels(destination: str, checkin: str = "2025-03-01", nights: int = 3) -> str:
    names = [f"Grand Hotel {destination}", f"The {destination} Inn", "Park View Suites", f"Budget Stay {destination}", f"Boutique {destination} House"]
    base_price = (sum(ord(c) for c in destination) % 80) + 60
    hotels = []
    for i, name in enumerate(names):
        price = base_price + (i * 30) + random.randint(-10, 20)
        stars = min(5, 2 + i)
        hotels.append({
            "hotel_id": f"HTL-{2000 + i}", "name": name, "stars": stars,
            "price_per_night_eur": price, "total_eur": price * nights,
            "rating": round(3.5 + (stars * 0.25) + random.uniform(-0.2, 0.3), 1),
            "amenities": ["WiFi", "Breakfast"] + (["Pool", "Gym"] if stars >= 4 else []),
            "rooms_available": random.randint(1, 12),
        })
    return json.dumps({"destination": destination, "checkin": checkin, "nights": nights, "hotels": hotels}, indent=2)


def mock_book_flight(flight_id: str, passenger_name: str) -> str:
    return json.dumps({"status": "confirmed", "booking_ref": f"BK-{random.randint(100000,999999)}", "flight_id": flight_id, "passenger": passenger_name}, indent=2)


def mock_book_hotel(hotel_id: str, guest_name: str, nights: int = 3) -> str:
    return json.dumps({"status": "confirmed", "booking_ref": f"HBK-{random.randint(100000,999999)}", "hotel_id": hotel_id, "guest": guest_name, "nights": nights}, indent=2)