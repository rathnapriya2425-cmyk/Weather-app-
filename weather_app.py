"""Weather App with Live OpenWeather API
Fetches real-time temperature, humidity and a 5-day forecast for any city.

Setup:
  1. pip install requests
  2. Create a free account at https://openweathermap.org and copy your API key
     (new keys can take up to 2 hours to activate).
  3. Run: python weather_app.py   (it will ask for the key the first time)
     Optional: set the OPENWEATHER_API_KEY environment variable to skip the prompt.
"""

import os
from collections import Counter, defaultdict
from datetime import datetime

import requests

BASE_URL = "https://api.openweathermap.org/data/2.5"
TIMEOUT = 10


# ---------------- REST API integration via requests ----------------
def call_api(endpoint, city, api_key):
    """Call an OpenWeather endpoint. Returns parsed JSON (dict) or None on failure."""
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT)
        if response.status_code == 401:
            print("  Invalid API key. Check it, or wait up to 2 hours if the key is new.")
        elif response.status_code == 404:
            print(f"  City '{city}' not found. Check the spelling (try 'Chennai' or 'Chennai,IN').")
        elif response.status_code == 429:
            print("  Too many requests. Wait a minute and try again.")
        elif response.ok:
            return response.json()  # JSON response parsing starts here
        else:
            print(f"  Server error: {response.status_code}")
    except requests.exceptions.Timeout:
        print("  The request timed out. Try again.")
    except requests.exceptions.ConnectionError:
        print("  No internet connection.")
    except requests.exceptions.RequestException as error:
        print(f"  Request failed: {error}")
    return None


# ---------------- JSON response parsing ----------------
def parse_current(data):
    """Pull the useful fields out of the /weather JSON response."""
    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "wind": data["wind"]["speed"],
        "description": data["weather"][0]["description"].title(),
    }


def parse_forecast(data):
    """Group the 3-hourly /forecast entries into one summary per day."""
    days = defaultdict(lambda: {"temps": [], "humidity": [], "desc": []})
    for entry in data["list"]:
        date = entry["dt_txt"].split(" ")[0]
        days[date]["temps"].append(entry["main"]["temp"])
        days[date]["humidity"].append(entry["main"]["humidity"])
        days[date]["desc"].append(entry["weather"][0]["description"].title())
    summary = []
    for date, d in sorted(days.items()):
        summary.append({
            "date": date,
            "min": min(d["temps"]),
            "max": max(d["temps"]),
            "humidity": round(sum(d["humidity"]) / len(d["humidity"])),
            "desc": Counter(d["desc"]).most_common(1)[0][0],
        })
    return summary


# ---------------- Clean CLI display ----------------
def show_current(w):
    print("\n" + "=" * 42)
    print(f" Weather in {w['city']}, {w['country']}")
    print("=" * 42)
    print(f" Condition   : {w['description']}")
    print(f" Temperature : {w['temp']:.1f} °C (feels like {w['feels_like']:.1f} °C)")
    print(f" Humidity    : {w['humidity']}%")
    print(f" Wind speed  : {w['wind']} m/s")


def show_forecast(days):
    print("\n 5-Day Forecast")
    print(f" {'Date':<12}{'Day':<6}{'Min':>6}{'Max':>7}{'Hum':>6}  Condition")
    print(" " + "-" * 56)
    for d in days[:5]:
        day = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%a")
        print(f" {d['date']:<12}{day:<6}{d['min']:>5.1f}°{d['max']:>6.1f}°{d['humidity']:>5}%  {d['desc']}")


def get_api_key():
    key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    while not key:
        key = input("Enter your OpenWeather API key: ").strip()
    return key


def main():
    print("=== Weather App (OpenWeather API) ===")
    api_key = get_api_key()
    while True:
        city = input("\nEnter city name (or 'q' to quit): ").strip()
        if city.lower() == "q":
            print("Goodbye!")
            break
        if not city:
            print("  Please type a city name.")
            continue

        current = call_api("weather", city, api_key)
        if current is None:
            continue
        show_current(parse_current(current))

        forecast = call_api("forecast", city, api_key)
        if forecast:
            show_forecast(parse_forecast(forecast))


if __name__ == "__main__":
    main()
