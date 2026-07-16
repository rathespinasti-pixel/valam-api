from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
)

from app.extensions import db, BLACKLISTED_TOKENS
from app.models.user import User
from app.utils.decorators import success_response, error_response, get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new farmer account.
    ---
    tags: [Auth]
    """
    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")

    if not full_name or not email or not password:
        return error_response("full_name, email and password are required", 400)

    if len(password) < 6:
        return error_response("Password must be at least 6 characters", 400)

    if User.query.filter_by(email=email.lower().strip()).first():
        return error_response("An account with this email already exists", 409)

    user = User(
        full_name=full_name.strip(),
        email=email.lower().strip(),
        phone=data.get("phone"),
        farm_location=data.get("farm_location"),
        farm_size_acres=data.get("farm_size_acres"),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        message="Account created successfully",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login user.
    ---
    tags: [Auth]
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return error_response("email and password are required", 400)

    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user or not user.check_password(password):
        return error_response("Invalid email or password", 401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        message="Login successful",
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout user (revokes current access token).
    ---
    tags: [Auth]
    """
    jti = get_jwt()["jti"]
    BLACKLISTED_TOKENS.add(jti)
    return success_response(message="Logged out successfully")


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Get current logged-in user.
    ---
    tags: [Auth]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict())


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update profile of the logged-in user.
    ---
    tags: [Auth]
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


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """
    Change password of the logged-in user.
    ---
    tags: [Auth]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return error_response("current_password and new_password are required", 400)

    if not user.check_password(current_password):
        return error_response("Current password is incorrect", 401)

    if len(new_password) < 6:
        return error_response("New password must be at least 6 characters", 400)

    user.set_password(new_password)
    db.session.commit()
    return success_response(message="Password changed successfully")
