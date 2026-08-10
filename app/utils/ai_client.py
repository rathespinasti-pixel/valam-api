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


def ask_ai_assistant(question: str, category: str | None = None, language: str = "en", user_context: dict = None) -> str:
    lang_name = "Tamil" if "ta" in (language or "").lower() else "Sinhala" if "si" in (language or "").lower() else "English"
    
    # 1. Try Primary Gemini / FarmingAssistantService with full user & crop context
    try:
        from app.services.farming_assistant_service import FarmingAssistantService
        enriched_q = f"Category: {category}. Question: {question}" if category else question
        return FarmingAssistantService.get_advice(enriched_q, language=lang_name, user_context=user_context)
    except Exception as gemini_err:
        print(f"Gemini Farming Assistant attempt failed: {gemini_err}. Trying fallback...")

    # 2. Fallback to Anthropic API if configured
    lang = (language or "en").lower()
    if "ta" in lang or "tamil" in lang:
        lang = "ta"
    elif "si" in lang or "sinhala" in lang:
        lang = "si"
    else:
        lang = "en"

    api_key = current_app.config.get("AI_PROVIDER_API_KEY") if current_app else None
    api_url = current_app.config.get("AI_PROVIDER_URL", "https://api.anthropic.com/v1/messages") if current_app else "https://api.anthropic.com/v1/messages"

    system_prompt = f"{SYSTEM_PROMPT} Respond 100% in language code {lang}."
    focus = CATEGORY_FOCUS.get((category or "").strip())
    if focus:
        system_prompt = f"{system_prompt} {focus}"

    if _is_valid_key(api_key):
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
            print(f"Anthropic Fallback notice: {exc}")

    # 3. Offline Agricultural Response Fallback
    if lang == "ta":
        return (
            "வளம் விவசாய AI உதவி:\n"
            "1. நேரடி விதைப்பு (Direct Seeding): ஏக்கருக்கு தேவையான விதை அளவு சோளம்: 8-10 கிகி, நெல்: 35-40 கிகி, தக்காளி: 200-250 கிராம்.\n"
            "2. நீர்ப்பாசனம்: 1 ஏக்கருக்கு ~4,000 மீட்டர் 16 மிமீ சொட்டுநீர் குழாய் மற்றும் 1.5 HP சூரிய மின்சார பம்ப் தேவை.\n"
            "3. உரம்: நிலத் தயாரிப்பில் ஏக்கருக்கு 8-10 டன் மக்கிய உரம் மற்றும் 50 கிகி வேப்பம் புண்ணாக்கு இடவும்."
        )
    elif lang == "si":
        return (
            "වළම් කෘෂිකාර්මික AI සහකරු:\n"
            "1. සෘජු බීජ වැපිරීම: අක්කරයකට බඩඉරිඟු 8-10 kg, වී 35-40 kg, තක්කාලි 200-250 g බීජ ප්‍රමාණයක් මිලදී ගන්න.\n"
            "2. ජලසම්පාදනය: අක්කරයකට මීටර් 4,000 ක බිංදු ජල බට සහ 1.5 HP සූර්ය ජල පොම්පයක් නිර්දේශ කෙරේ.\n"
            "3. පොහොර: මූලික අවස්ථාවේදී අක්කරයකට කොම්පෝස්ට් ටොන් 8-10 ක් යොදන්න."
        )
    else:
        return (
            "Valam Agricultural & Seeding Estimation Guide:\n"
            "1. Direct Seeding Purchase: For 1 acre, buy Maize (8-10 kg), Paddy (30-40 kg), Tomato (200-250 g), Chilli (400-500 g).\n"
            "2. Drip & Solar Sizing: 1 acre requires approx. 4,000m of 16mm lateral drip tube, 4,000-6,000 L/day water, and a 1.5 HP solar pump.\n"
            "3. Stage Compost: Apply 8-10 tons/acre decomposed organic manure + 50kg Neem cake as basal land preparation."
        )
