from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.diagnosis_controller import (
    analyze_disease,
    get_diagnosis_history,
)

diagnosis_bp = Blueprint("diagnosis", __name__)

diagnosis_bp.add_url_rule("/analyze", view_func=jwt_required()(analyze_disease), methods=["POST"])
diagnosis_bp.add_url_rule("/history", view_func=jwt_required()(get_diagnosis_history), methods=["GET"])
