from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.chatbot_controller import (
    ask,
    history,
    delete_history,
)

chatbot_bp = Blueprint("chatbot", __name__)

chatbot_bp.add_url_rule("/ask", view_func=jwt_required()(ask), methods=["POST"])
chatbot_bp.add_url_rule("/history", view_func=jwt_required()(history), methods=["GET"])
chatbot_bp.add_url_rule("/history/<int:history_id>", view_func=jwt_required()(delete_history), methods=["DELETE"])
