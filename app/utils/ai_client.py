"""
Thin wrapper around an AI provider for the farming assistant.
Provides localized agricultural Q&A and plant disease advisory fallback if no key is configured.
"""

import requests
from flask import current_app

SYSTEM_PROMPT = (
    "You are Valam's agricultural AI assistant for farmers in Vavuniya, Sri Lanka. "
    "Give practical, concise, safe advice regarding crop management, pests, irrigation, and soil health."
)

CATEGORY_FOCUS = {
    "weather": "Focus on rainfall, temperature, irrigation timing and weather-related farming alerts.",
    "crop-guides": "Focus on soil preparation, sowing, feeding schedules and harvest timing for vegetables, rice and spices.",
    "ai-chatbot": "Focus on identifying pests/diseases from symptoms described and recommending organic & chemical treatment.",
    "irrigation-solar": "Focus on drip irrigation, solar pump setups, and dry-zone water conservation.",
}


def _is_valid_key(key: str | None) -> bool:
    if not key or not isinstance(key, str):
        return False
    k = key.strip()
    return bool(k and k != "your-ai-provider-api-key" and not k.startswith("your-"))


def ask_ai_assistant(question: str, category: str | None = None) -> str:
    api_key = current_app.config.get("AI_PROVIDER_API_KEY")
    api_url = current_app.config.get("AI_PROVIDER_URL", "https://api.anthropic.com/v1/messages")

    system_prompt = SYSTEM_PROMPT
    focus = CATEGORY_FOCUS.get((category or "").strip())
    if focus:
        system_prompt = f"{SYSTEM_PROMPT} {focus}"

    if not _is_valid_key(api_key):
        q_lower = question.lower()
        if "yellow" in q_lower or "spot" in q_lower or "blight" in q_lower or "wilt" in q_lower:
            return (
                "Based on the reported symptoms (leaf yellowing / spots):\n"
                "1. Possible Cause: Early Blight or Nitrogen / Iron Nutrient Deficiency commonly seen in dry-zone solanaceous crops (Tomato/Chili).\n"
                "2. Immediate Actions: Remove infected bottom leaves, avoid overhead hose watering, and apply a 5% Neem seed kernel extract or copper-based fungicide spray.\n"
                "3. Prevention: Maintain proper plant spacing (60cm x 45cm) and irrigate early in the morning."
            )
        return (
            f"Regarding your query ('{question}'): For crops in Vavuniya, ensure proper field drainage during Maha rainy season, "
            "and utilize drip irrigation with straw mulching during Yala dry season. Apply recommended NPK basal fertilizer "
            "and inspect leaves weekly for early thrips or mite infestations."
        )

    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 600,
        "system": system_prompt,
        "messages": [{"role": "user", "content": question}],
    }

    try:
        resp = requests.post(api_url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        parts = [c["text"] for c in data.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts).strip() or "Valam Assistant: Please consult your local ASC extension officer for specific guidance."
    except Exception as exc:
        print(f"AI Provider fallback notice: {exc}")
        return (
            f"Valam Agricultural Guidance (Offline Advice for '{question}'): "
            "Maintain soil organic matter using compost, ensure early morning irrigation, "
            "and spray neem oil extract for sap-sucking pest control."
        )
