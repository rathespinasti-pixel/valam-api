from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.models.user import User


def get_current_user():
    """Fetch the User row for the currently authenticated JWT identity."""
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(int(user_id))


def require_owner_or_admin(get_owner_id):
    """
    Decorator factory: ensures the logged-in user either owns the resource
    (owner_id returned by get_owner_id(*args, **kwargs)) or has an admin role.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            if current_user is None:
                return jsonify({"success": False, "message": "User not found"}), 404

            owner_id = get_owner_id(*args, **kwargs)
            if current_user.role != "admin" and current_user.id != owner_id:
                return jsonify({"success": False, "message": "Forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def success_response(data=None, message="Success", status_code=200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(message="Error", status_code=400, errors=None):
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status_code
