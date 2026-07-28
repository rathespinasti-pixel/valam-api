"""
Agro Advisory engine: converts weather metrics into practical farming advice.
"""

def generate_agro_advisory(location: str, current_weather: dict, forecast_data: dict | None = None) -> list[dict]:
    advisories = []
    
    temp = current_weather.get("temperature_c", 28)
    humidity = current_weather.get("humidity_percent", 70)
    condition = (current_weather.get("condition") or "").lower()
    wind_kmh = current_weather.get("wind_kmh", 10)

    # Check forecast for rain expectation
    rain_expected = False
    if forecast_data and "days" in forecast_data:
        for day in forecast_data["days"]:
            cond = (day.get("condition") or "").lower()
            if "rain" in cond or "shower" in cond or "storm" in cond:
                rain_expected = True
                break
    elif "rain" in condition or "shower" in condition or "thunderstorm" in condition:
        rain_expected = True

    # 1. Pesticide & Fertilizer Spraying Advice
    if rain_expected:
        advisories.append({
            "category": "Pesticides & Chemical Care",
            "title": "Avoid Spraying Today",
            "severity": "warning",
            "advice": "Rain is expected in the region. Postpone foliar fertilizer or chemical pesticide application to prevent wash-off.",
        })
    elif wind_kmh > 20:
        advisories.append({
            "category": "Pesticides & Chemical Care",
            "title": "High Wind Drift Risk",
            "severity": "warning",
            "advice": f"Wind speed is {wind_kmh} km/h. Avoid pesticide spraying during high wind hours to prevent spray drift.",
        })
    else:
        advisories.append({
            "category": "Pesticides & Chemical Care",
            "title": "Suitable for Spraying",
            "severity": "info",
            "advice": "Calm weather conditions. Ideal for scheduled fertilizer application and organic pest sprays in early morning.",
        })

    # 2. Irrigation Advice
    if rain_expected:
        advisories.append({
            "category": "Irrigation Management",
            "title": "Reduce Irrigation",
            "severity": "info",
            "advice": "Upcoming precipitation detected. Hold off on heavy drip or surface irrigation to save water and prevent root waterlogging.",
        })
    elif temp > 32:
        advisories.append({
            "category": "Irrigation Management",
            "title": "Increase Evapotranspiration Protection",
            "severity": "warning",
            "advice": f"High temperatures around {temp}°C. Water crops early in the morning or late afternoon to minimize evaporation loss.",
        })
    else:
        advisories.append({
            "category": "Irrigation Management",
            "title": "Normal Irrigation Schedule",
            "severity": "info",
            "advice": "Maintain standard soil moisture levels for active growth stages.",
        })

    # 3. Pest & Disease Alert
    if humidity > 80:
        advisories.append({
            "category": "Disease Alert",
            "title": "High Fungal Risk",
            "severity": "warning",
            "advice": f"High humidity level ({humidity}%). Monitor crops like Tomato, Chili, and Brinjal closely for leaf blight, damping-off, or powdery mildew.",
        })
    elif temp > 30 and humidity < 50:
        advisories.append({
            "category": "Pest Alert",
            "title": "Sucking Pest Risk",
            "severity": "warning",
            "advice": "Hot and dry conditions favor thrips and spider mite infestations on young crops. Inspect under leaves regularly.",
        })

    # 4. Nursery & General Field Advice
    if temp > 33:
        advisories.append({
            "category": "Nursery & Crop Protection",
            "title": "Shade Young Seedlings",
            "severity": "warning",
            "advice": "Extreme heat warning. Provide shade nets or straw mulching for delicate vegetable nurseries.",
        })

    return advisories
