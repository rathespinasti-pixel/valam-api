import logging
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

DISEASE_EXPLANATION_SYSTEM_PROMPT = """
You are a plant pathology expert for Sri Lankan farmers.
Your job is to convert technical plant disease information into simple, easy-to-understand farmer guidance.

Format your output into clear, structured sections:
1. 📌 Disease Explanation (Simple overview of what is happening to the plant)
2. 🔍 Possible Causes (Why this disease occurs, e.g. high moisture, fungus, insect vector)
3. 🚨 Immediate Actions (What the farmer should do today)
4. 🌿 Organic Treatment Suggestions (Natural remedies, neem oil, organic sprays)
5. 🧪 Chemical Treatment Suggestions (Safe recommended products with strict safety rules, if applicable)
6. 🛡️ Prevention Tips (How to prevent this in future seasons)

Keep language simple, practical, and safe.
"""

class DiseaseExplanationService:
    """Service generating farmer-friendly disease explanations."""

    @classmethod
    def explain_disease(cls, crop: str, disease: str, analysis: str = "", symptoms: str = "", language: str = "English") -> str:
        if not crop or not disease:
            raise ValueError("Crop name and disease name are required.")

        prompt = f"""
Crop Name: {crop}
Disease Identified: {disease}
Symptoms Reported: {symptoms or 'Not specified'}
Image Analysis Details: {analysis or 'No image analysis available'}

Explain this disease clearly for a farmer according to your structured format.
"""
        raw_explanation = GeminiService.generate_content(
            prompt=prompt,
            system_instruction=DISEASE_EXPLANATION_SYSTEM_PROMPT,
            temperature=0.5
        )

        final_explanation = TranslationService.translate(raw_explanation, target_language=language)
        return final_explanation
