from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.disease_diagnosis import DiseaseDiagnosis
from app.utils.decorators import success_response, error_response, get_current_user
from app.utils.ai_client import ask_ai_assistant

diagnosis_bp = Blueprint("diagnosis", __name__, url_prefix="/api/diagnosis")


@diagnosis_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_disease():
    """Diagnose pest/disease issue using symptoms and optional crop image."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    symptoms = (data.get("symptoms") or "").strip()
    crop_name = (data.get("crop_name") or "Crop").strip()
    image_url = data.get("image_url")

    if not symptoms:
        return error_response("symptoms description is required", 400)

    prompt = (
        f"A farmer in Vavuniya, Sri Lanka reported a problem with their {crop_name}.\n"
        f"Observed Symptoms: {symptoms}\n"
        f"Image URL provided: {image_url if image_url else 'None'}\n\n"
        "Please provide a structured response with:\n"
        "1. Possible Disease/Pest Issue\n"
        "2. Likely Causes\n"
        "3. Recommended Organic & Chemical Control Actions\n"
        "4. Prevention Tips for Vavuniya Climate"
    )

    diagnosis_text = ask_ai_assistant(prompt, category="ai-chatbot")

    recommendation_text = (
        "1. Isolate affected plants if severe.\n"
        "2. Apply recommended organic neem spray or targeted fungicide.\n"
        "3. Ensure proper drainage and air circulation between rows."
    )

    entry = DiseaseDiagnosis(
        user_id=user.id,
        crop_name=crop_name,
        image_url=image_url,
        symptoms=symptoms,
        diagnosis_result=diagnosis_text,
        recommendations=recommendation_text,
    )
    db.session.add(entry)
    db.session.commit()

    return success_response(entry.to_dict(), message="Diagnosis generated successfully", status_code=201)


@diagnosis_bp.route("/history", methods=["GET"])
@jwt_required()
def get_diagnosis_history():
    """List previous diagnosis records for current user."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    query = DiseaseDiagnosis.query.filter_by(user_id=user.id).order_by(DiseaseDiagnosis.created_at.desc())
    items = query.limit(20).all()

    return success_response([item.to_dict() for item in items])
