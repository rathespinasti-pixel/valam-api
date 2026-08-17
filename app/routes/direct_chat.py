from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.direct_chat_controller import (
    get_conversations,
    get_messages,
    send_message,
)

direct_chat_bp = Blueprint("direct_chat", __name__)

direct_chat_bp.add_url_rule("/conversations", view_func=jwt_required()(get_conversations), methods=["GET"])
direct_chat_bp.add_url_rule("/messages/<int:other_user_id>", view_func=jwt_required()(get_messages), methods=["GET"])
direct_chat_bp.add_url_rule("/send", view_func=jwt_required()(send_message), methods=["POST"])
