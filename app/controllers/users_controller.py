from flask import request

from app.extensions import db
from app.models.user import User
from app.utils.decorators import success_response, error_response, get_current_user


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
    fields = (
        "full_name", "phone", "farm_location", "farm_size_acres",
        "district_asc", "farmer_type", "farming_experience",
        "main_crops_grown", "preferred_language", "onboarding_completed",
        "farming_category", "district", "ds_division", "gn_division",
        "land_size", "land_size_unit", "irrigation_preference", "fertilizer_preference"
    )
    for field in fields:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return success_response(user.to_dict(), message="Profile updated successfully")


def save_onboarding():
    """
    Save farmer onboarding preferences.
    ---
    tags: [Users]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    fields = (
        "full_name", "phone", "farm_location", "farm_size_acres",
        "district_asc", "farmer_type", "farming_experience",
        "main_crops_grown", "preferred_language",
        "farming_category", "district", "ds_division", "gn_division",
        "land_size", "land_size_unit", "irrigation_preference", "fertilizer_preference"
    )
    for field in fields:
        if field in data:
            setattr(user, field, data[field])

    user.onboarding_completed = True
    db.session.commit()

    return success_response(user.to_dict(), message="Onboarding profile completed successfully")


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
