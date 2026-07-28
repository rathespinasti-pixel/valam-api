"""
Thin wrapper around an AI provider for the farming chatbot.

By default this calls the Anthropic Messages API using the
AI_PROVIDER_API_KEY / AI_PROVIDER_URL from config. If no API key is
configured, it falls back to a canned response so the endpoint still
works out of the box during development/testing.
"""

import requests
from flask import current_app

SYSTEM_PROMPT = (
    "You are an expert agricultural and solar-farming assistant. "
    "Give practical, concise, safe advice to farmers. If a question is "
    "outside farming/agriculture/solar topics, politely redirect the user."
)

# Extra focus appended to the system prompt when the frontend tags a
# question with the feature/topic the user opened the chatbot from.
CATEGORY_FOCUS = {
    "weather": (
        "The user opened the chatbot from the Weather Forecast feature. "
        "Focus on rainfall, temperature, irrigation timing and weather-related "
        "farming alerts."
    ),
    "crop-guides": (
        "The user opened the chatbot from the Crop Guides feature. Focus on "
        "soil preparation, sowing, feeding schedules and harvest timing for "
        "vegetables, fruits, rice and spices."
    ),
    "ai-chatbot": (
        "The user opened the chatbot from the AI Chatbot & Plant Disease "
        "Detection feature. Focus on identifying pests/diseases from symptoms "
        "described and recommending treatment."
    ),
    "pest-radar": (
        "The user opened the chatbot as a follow-up to Valam's Acoustic Radar "
        "(AI pest detection from insect sound recordings). A pest name and "
        "infestation risk level may be mentioned in their question — focus on "
        "explaining that pest's causes, prevention methods and treatment or "
        "biological/pesticide control options for the crops it affects."
    ),
    "irrigation-solar": (
        "The user opened the chatbot from the Irrigation & Solar Farming "
        "feature. Focus on drip/sprinkler irrigation, solar pump setups, "
        "costs and subsidy eligibility."
    ),
    "marketplace": (
        "The user opened the chatbot from the Seeds & Fertilizer Marketplace "
        "feature. Focus on buying/selling seeds, fertilizer and organic "
        "products, and fair pricing."
    ),
}


def ask_ai_assistant(question: str, category: str | None = None) -> str:
    api_key = current_app.config.get("AI_PROVIDER_API_KEY")
    api_url = current_app.config.get("AI_PROVIDER_URL")

    system_prompt = SYSTEM_PROMPT
    focus = CATEGORY_FOCUS.get((category or "").strip())
    if focus:
        system_prompt = f"{SYSTEM_PROMPT} {focus}"

    if not api_key:
        return (
            "AI assistant is not configured yet. Please set AI_PROVIDER_API_KEY "
            "in your environment. (This is a placeholder response.) "
            f"You asked: '{question}'"
        )

    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": system_prompt,
        "messages": [{"role": "user", "content": question}],
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        parts = [c["text"] for c in data.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts).strip() or "Sorry, I couldn't generate a response."
    except requests.RequestException as exc:
        return f"AI assistant is temporarily unavailable ({exc}). Please try again later."
