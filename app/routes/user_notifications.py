from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.user_notifications_controller import (
    get_user_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)

user_notifications_bp = Blueprint("user_notifications", __name__)

user_notifications_bp.add_url_rule("", view_func=jwt_required()(get_user_notifications), methods=["GET"])
user_notifications_bp.add_url_rule("/<int:notif_id>/read", view_func=jwt_required()(mark_notification_read), methods=["PUT"])
user_notifications_bp.add_url_rule("/read-all", view_func=jwt_required()(mark_all_notifications_read), methods=["PUT"])
