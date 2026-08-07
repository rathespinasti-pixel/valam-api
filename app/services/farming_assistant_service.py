import logging
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

FARMING_ASSISTANT_SYSTEM_PROMPT = """
You are an expert, friendly AI Farming Assistant specialized in Sri Lankan agriculture.
Your role is to guide small and medium farmers with practical, safe, and easy-to-understand advice.

Key Instructions:
1. Provide simple explanations without overly complex jargon.
2. Focus on crops commonly grown in Sri Lanka (e.g., Chilli, Brinjal / Eggplant, Tomato, Paddy / Rice, Red Onion, Maize, Coconut, Papaya, Banana).
3. Offer actionable, practical steps that farmers can immediately perform.
4. Prioritize organic solutions, safe watering, proper spacing, soil health, and balanced fertilization.
5. Provide safe recommendations. NEVER recommend hazardous chemical usage without emphasizing protective equipment (gloves, mask) and exact dosage rules.
6. Keep tone warm, encouraging, and supportive.
"""

class FarmingAssistantService:
    """Service handling AI farming queries tailored for Sri Lankan farmers."""

    @classmethod
    def get_advice(cls, question: str, language: str = "English") -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        prompt = f"""
Farmer Question: "{question.strip()}"

Please answer as a Sri Lankan farming assistant following your core instructions.
Give clear step-by-step advice.
"""
        # Get raw response from Gemini
        response_text = GeminiService.generate_content(
            prompt=prompt,
            system_instruction=FARMING_ASSISTANT_SYSTEM_PROMPT,
            temperature=0.6
        )

        # Translate to desired language if needed
        final_answer = TranslationService.translate(response_text, target_language=language)
        return final_answer
