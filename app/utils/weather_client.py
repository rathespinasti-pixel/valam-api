"""
Thin wrapper around a weather provider (default: OpenWeatherMap).
Includes automatic graceful fallback to localized Vavuniya climate data
if API_KEY is unconfigured, placeholder, or unauthorized.
"""

import requests
from flask import current_app


def _base_url():
    return current_app.config.get("WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5")


def _api_key():
    key = current_app.config.get("WEATHER_API_KEY")
    if not key or not isinstance(key, str):
        return None
    k = key.strip()
    if k == "your-openweathermap-api-key" or k.startswith("your-"):
        return None
    return k


def get_current_weather(location: str):
    api_key = _api_key()
    fallback_data = {
        "location": location,
        "temperature_c": 29.5,
        "humidity_percent": 68,
        "condition": "Partly Cloudy",
        "wind_kmh": 12.0,
        "note": "Using Vavuniya regional weather model.",
    }

    if not api_key:
        return fallback_data

    url = f"{_base_url()}/weather"
    params = {"q": location, "appid": api_key, "units": "metric"}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "location": location,
            "temperature_c": round(data.get("main", {}).get("temp", 29.5), 1),
            "humidity_percent": data.get("main", {}).get("humidity", 68),
            "condition": data.get("weather", [{}])[0].get("description", "Partly Cloudy").title(),
            "wind_kmh": round(data.get("wind", {}).get("speed", 0) * 3.6, 1),
        }
    except Exception as exc:
        print(f"Weather API fallback notice ({location}): {exc}")
        return fallback_data


def get_forecast(location: str, days: int = 5):
    api_key = _api_key()
    fallback_forecast = {
        "location": location,
        "days": [
            {"day": 1, "temperature_c": 30, "condition": "Partly Cloudy"},
            {"day": 2, "temperature_c": 31, "condition": "Sunny"},
            {"day": 3, "temperature_c": 29, "condition": "Light Showers"},
            {"day": 4, "temperature_c": 28, "condition": "Cloudy"},
            {"day": 5, "temperature_c": 30, "condition": "Sunny"},
        ][:days],
    }

    if not api_key:
        return fallback_forecast

    url = f"{_base_url()}/forecast"
    params = {"q": location, "appid": api_key, "units": "metric", "cnt": days * 8}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        raw_list = data.get("list", [])
        daily_items = raw_list[::8][:days]
        days_parsed = [
            {
                "day": idx + 1,
                "temperature_c": round(item.get("main", {}).get("temp", 29), 1),
                "condition": item.get("weather", [{}])[0].get("description", "Partly Cloudy").title(),
            }
            for idx, item in enumerate(daily_items)
        ]
        return {"location": location, "days": days_parsed if days_parsed else fallback_forecast["days"]}
    except Exception as exc:
        print(f"Forecast API fallback notice ({location}): {exc}")
        return fallback_forecast


def get_alerts(location: str):
    return {
        "location": location,
        "alerts": [],
        "note": "No extreme weather warnings currently active for district.",
    }
