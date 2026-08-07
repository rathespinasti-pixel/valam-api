from flask import Blueprint, request, jsonify
from app.services.gemini_service import GeminiServiceError
from app.services.farming_assistant_service import FarmingAssistantService
from app.services.disease_explanation_service import DiseaseExplanationService
from app.services.translation_service import TranslationService

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/farming-assistant", methods=["POST"])
def farming_assistant():
    """
    POST /api/ai/farming-assistant
    Request JSON: { "question": string, "language": string }
    Response JSON: { "answer": string }
    """
    data = request.get_json() or {}
    question = data.get("question")
    language = data.get("language", "English")

    if not question or not str(question).strip():
        return jsonify({"success": False, "message": "Question is required."}), 400

    try:
        answer = FarmingAssistantService.get_advice(question=question, language=language)
        return jsonify({
            "success": True,
            "answer": answer
        }), 200
    except GeminiServiceError as ge:
        return jsonify({
            "success": False,
            "message": f"AI Assistant Service temporarily unavailable: {str(ge)}"
        }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate farming advice: {str(e)}"
        }), 500


@ai_bp.route("/disease-explanation", methods=["POST"])
def disease_explanation():
    """
    POST /api/ai/disease-explanation
    Request JSON: { "crop": string, "disease": string, "analysis": string, "symptoms": string, "language": string }
    Response JSON: { "explanation": string }
    """
    data = request.get_json() or {}
    crop = data.get("crop")
    disease = data.get("disease")
    analysis = data.get("analysis", "")
    symptoms = data.get("symptoms", "")
    language = data.get("language", "English")

    if not crop or not str(crop).strip():
        return jsonify({"success": False, "message": "Crop name is required."}), 400
    if not disease or not str(disease).strip():
        return jsonify({"success": False, "message": "Disease name is required."}), 400

    try:
        explanation = DiseaseExplanationService.explain_disease(
            crop=crop,
            disease=disease,
            analysis=analysis,
            symptoms=symptoms,
            language=language
        )
        return jsonify({
            "success": True,
            "explanation": explanation
        }), 200
    except GeminiServiceError as ge:
        return jsonify({
            "success": False,
            "message": f"AI Disease Service temporarily unavailable: {str(ge)}"
        }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate disease explanation: {str(e)}"
        }), 500


@ai_bp.route("/translate", methods=["POST"])
def translate():
    """
    POST /api/ai/translate
    Request JSON: { "text": string, "target_language": string }
    Response JSON: { "translated_text": string }
    """
    data = request.get_json() or {}
    text = data.get("text")
    target_language = data.get("target_language") or data.get("language") or "English"

    if not text or not str(text).strip():
        return jsonify({"success": False, "message": "Text to translate is required."}), 400

    try:
        translated_text = TranslationService.translate(text=text, target_language=target_language)
        return jsonify({
            "success": True,
            "translated_text": translated_text
        }), 200
    except GeminiServiceError as ge:
        return jsonify({
            "success": False,
            "message": f"Translation Service temporarily unavailable: {str(ge)}"
        }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to translate text: {str(e)}"
        }), 500
