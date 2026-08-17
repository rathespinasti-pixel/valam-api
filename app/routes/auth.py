from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.auth_controller import (
    register,
    login,
    logout,
    refresh,
    me,
    update_profile,
    change_password,
)

auth_bp = Blueprint("auth", __name__)

auth_bp.add_url_rule("/register", view_func=register, methods=["POST"])
auth_bp.add_url_rule("/login", view_func=login, methods=["POST"])
auth_bp.add_url_rule("/logout", view_func=jwt_required()(logout), methods=["POST"])
auth_bp.add_url_rule("/refresh", view_func=jwt_required(refresh=True)(refresh), methods=["POST"])
auth_bp.add_url_rule("/me", view_func=jwt_required()(me), methods=["GET"])
auth_bp.add_url_rule("/profile", view_func=jwt_required()(update_profile), methods=["PUT"])
auth_bp.add_url_rule("/change-password", view_func=jwt_required()(change_password), methods=["PUT"])
