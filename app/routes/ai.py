from flask import Blueprint

from app.controllers.ai_controller import (
    farming_assistant,
    disease_explanation,
    translate,
)

ai_bp = Blueprint("ai", __name__)

ai_bp.add_url_rule("/farming-assistant", view_func=farming_assistant, methods=["POST"])
ai_bp.add_url_rule("/disease-explanation", view_func=disease_explanation, methods=["POST"])
ai_bp.add_url_rule("/translate", view_func=translate, methods=["POST"])
