from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.users_controller import (
    get_profile,
    update_profile,
    save_onboarding,
    view_user,
    delete_user,
)

users_bp = Blueprint("users", __name__)

users_bp.add_url_rule("/profile", view_func=jwt_required()(get_profile), methods=["GET"])
users_bp.add_url_rule("/profile", view_func=jwt_required()(update_profile), methods=["PUT"])
users_bp.add_url_rule("/onboarding", view_func=jwt_required()(save_onboarding), methods=["POST"])
users_bp.add_url_rule("/<int:user_id>", view_func=jwt_required()(view_user), methods=["GET"])
users_bp.add_url_rule("/<int:user_id>", view_func=jwt_required()(delete_user), methods=["DELETE"])
