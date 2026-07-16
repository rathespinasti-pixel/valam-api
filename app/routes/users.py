from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.user import User
from app.utils.decorators import success_response, error_response, get_current_user

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """
    Get logged-in user's profile.
    ---
    tags: [Users]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict())


@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update logged-in user's profile.
    ---
    tags: [Users]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    for field in ("full_name", "phone", "farm_location", "farm_size_acres"):
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return success_response(user.to_dict(), message="Profile updated successfully")


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def view_user(user_id):
    """
    View a user's public profile by id.
    ---
    tags: [Users]
    """
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict())


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """
    Delete a user account. Only the account owner or an admin may do this.
    ---
    tags: [Users]
    """
    current_user = get_current_user()
    if not current_user:
        return error_response("User not found", 404)

    if current_user.id != user_id and current_user.role != "admin":
        return error_response("Forbidden", 403)

    target = User.query.get(user_id)
    if not target:
        return error_response("User not found", 404)

    db.session.delete(target)
    db.session.commit()
    return success_response(message="Account deleted successfully")
