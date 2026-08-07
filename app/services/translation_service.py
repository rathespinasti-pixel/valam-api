import logging
from app.services.gemini_service import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)

TRANSLATION_SYSTEM_PROMPT = """
You are a professional agricultural translator for Sri Lankan languages (Tamil, Sinhala, English).

Instructions:
- If target language is Tamil (தமிழ்): Translate the entire text into clean, standard Tamil suitable for farmers. Do not mix English words unnecessarily unless it is a specific proper noun or chemical name. Use clear Tamil agricultural terminology.
- If target language is Sinhala (සිංහල): Translate the entire text into clean, standard Sinhala suitable for farmers. Do not mix English words unnecessarily. Use clear Sinhala agricultural terminology.
- If target language is English: Ensure the text is written in clear, standard English.

Maintain original markdown formatting, headers, lists, and bullet points.
"""

class TranslationService:
    """Service handling multi-lingual translations (English, Tamil, Sinhala)."""

    @classmethod
    def translate(cls, text: str, target_language: str = "English") -> str:
        if not text or not text.strip():
            return ""

        lang_lower = (target_language or "english").strip().lower()

        # If already English or default, check if text is non-empty
        if lang_lower in ["en", "english"]:
            return text.strip()

        # Map language string
        if lang_lower in ["ta", "tamil", "தமிழ்"]:
            target_lang_name = "Tamil (தமிழ்)"
        elif lang_lower in ["si", "sinhala", "සිංහල"]:
            target_lang_name = "Sinhala (සිංහල)"
        else:
            target_lang_name = target_language

        prompt = f"""
Target Language: {target_lang_name}

Text to Translate:
\"\"\"
{text.strip()}
\"\"\"
"""
        try:
            translated = GeminiService.generate_content(
                prompt=prompt,
                system_instruction=TRANSLATION_SYSTEM_PROMPT,
                temperature=0.3
            )
            return translated if translated else text
        except Exception as e:
            logger.error(f"Translation to {target_language} failed: {str(e)}")
            # Fallback to original text on error
            return text
