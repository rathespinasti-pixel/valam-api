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


def ask_ai_assistant(question: str, category: str | None = None, language: str = "en") -> str:
    lang = (language or "en").lower()
    if "ta" in lang or "tamil" in lang:
        lang = "ta"
    elif "si" in lang or "sinhala" in lang:
        lang = "si"
    else:
        lang = "en"

    api_key = current_app.config.get("AI_PROVIDER_API_KEY")
    api_url = current_app.config.get("AI_PROVIDER_URL", "https://api.anthropic.com/v1/messages")

    system_prompt = f"{SYSTEM_PROMPT} Respond 100% in language code {lang}."
    focus = CATEGORY_FOCUS.get((category or "").strip())
    if focus:
        system_prompt = f"{system_prompt} {focus}"

    if not _is_valid_key(api_key):
        if lang == "ta":
            return (
                "வளம் விவசாய AI உதவி:\n"
                "1. நீர்ப்பாசனம்: மகா பருவத்தில் வடிகால் வசதிகளை மேம்படுத்துங்கள். யால பருவத்தில் சொட்டுநீர் பாசனத்தைப் பயன்படுத்துங்கள்.\n"
                "2. உரம் & நோய்: 5% வேப்பங் கொட்டை சாறு தெளித்து பூச்சிகளைக் கட்டுப்படுத்துங்கள். தகுந்த NPK உரமிடுங்கள்.\n"
                "3. பயிர் இடைவெளி: பயிர் வளர்ச்சிக்கு 60செ.மீ x 45செ.மீ இடைவெளியைப் பேணுங்கள்."
            )
        elif lang == "si":
            return (
                "වළම් කෘෂිකාර්මික AI සහකරු:\n"
                "1. ජලසම්පාදනය: මහා කන්නයේදී ජලාපවහනය නිසි ලෙස පවත්වා ගන්න. යල කන්නයේදී බිංදු ජලසම්පාදනය භාවිතා කරන්න.\n"
                "2. පොහොර සහ පලිබෝධ: 5% කොහොඹ ඇට සාරය යොදා පලිබෝධ පාලනය කරන්න. නිර්දේශිත NPK පොහොර යොදන්න.\n"
                "3. පරතරය: නිසි පැළ පරතරය (60cm x 45cm) පවත්වා ගන්න."
            )
        else:
            return (
                "Valam Agricultural AI Guidance:\n"
                "1. Irrigation: Ensure proper field drainage during Maha rainy season, and utilize drip irrigation with mulching during Yala dry season.\n"
                "2. Fertilizer & Pests: Apply recommended NPK basal fertilizer and spray 5% neem seed kernel extract for sap-sucking pest control.\n"
                "3. Spacing: Maintain recommended plant spacing (60cm x 45cm) for optimal airflow."
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
