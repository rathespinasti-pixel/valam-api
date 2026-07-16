"""
Thin wrapper around a weather provider (default: OpenWeatherMap).
Set WEATHER_API_KEY in your environment to enable live data.
"""

import requests
from flask import current_app


def _base_url():
    return current_app.config.get("WEATHER_API_BASE_URL")


def _api_key():
    return current_app.config.get("WEATHER_API_KEY")


def get_current_weather(location: str):
    api_key = _api_key()
    if not api_key:
        return {
            "location": location,
            "note": "WEATHER_API_KEY not configured - showing placeholder data.",
            "temperature_c": 27.0,
            "humidity_percent": 65,
            "condition": "Partly Cloudy",
            "wind_kmh": 12,
        }

    url = f"{_base_url()}/weather"
    params = {"q": location, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return {
        "location": location,
        "temperature_c": data.get("main", {}).get("temp"),
        "humidity_percent": data.get("main", {}).get("humidity"),
        "condition": data.get("weather", [{}])[0].get("description"),
        "wind_kmh": round(data.get("wind", {}).get("speed", 0) * 3.6, 1),
    }


def get_forecast(location: str, days: int = 7):
    api_key = _api_key()
    if not api_key:
        return {
            "location": location,
            "note": "WEATHER_API_KEY not configured - showing placeholder data.",
            "days": [
                {"day": i + 1, "temperature_c": 26 + i % 3, "condition": "Sunny"}
                for i in range(days)
            ],
        }

    url = f"{_base_url()}/forecast"
    params = {"q": location, "appid": api_key, "units": "metric", "cnt": days * 8}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return {"location": location, "raw_forecast_list": data.get("list", [])}


def get_alerts(location: str):
    # OpenWeatherMap's free "weather" endpoint doesn't include alerts;
    # the "onecall" endpoint (with lat/lon) does. This is a simplified
    # placeholder that can be swapped for a real alerts data source.
    return {
        "location": location,
        "alerts": [],
        "note": "No active alerts, or alerts provider not configured.",
    }
