from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.user import User
from app.models.crop_guide import CropGuide
from app.models.admin_activity_log import AdminActivityLog
from app.utils.decorators import success_response, error_response, get_current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def log_admin_action(admin, action: str, details: str):
    """Helper to record audit trail of admin operations."""
    try:
        log = AdminActivityLog(
            action=action,
            performed_by=admin.full_name or admin.email,
            performed_by_id=admin.id,
            details=details,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error recording admin activity log: {e}")


# =========================================================
# 1. USER MANAGEMENT ENDPOINTS
# =========================================================

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def get_admin_users():
    """List users with search, category, district, status filtering & pagination."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    district = request.args.get("district", "").strip()
    status_filter = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.query

    if search:
        s = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(s)) | (User.email.ilike(s)) | (User.phone.ilike(s))
        )

    if category and category != "All":
        query = query.filter(User.farming_category.ilike(category))

    if district and district != "All":
        query = query.filter(User.district.ilike(district))

    if status_filter and status_filter != "All":
        query = query.filter(User.status == status_filter.lower())

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        "items": [u.to_dict() for u in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    })


@admin_bp.route("/users/<int:user_id>/ban", methods=["PUT"])
@jwt_required()
def ban_unban_user(user_id):
    """Toggle Ban / Unban status for a user."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response("User not found", 404)

    # Protect Super Admin from being banned
    if target_user.role == "super_admin":
        return error_response("Cannot ban Super Admin account", 400)

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ["active", "banned"]:
        new_status = "banned" if target_user.status == "active" else "active"

    target_user.status = new_status
    db.session.commit()

    action_label = "User Banned" if new_status == "banned" else "User Unbanned"
    log_admin_action(current_user, action_label, f"Changed status of {target_user.email} to {new_status}")

    return success_response(
        target_user.to_dict(),
        message=f"User status updated to {new_status}"
    )


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_admin_user(user_id):
    """Permanently delete a user account."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required to delete users", 403)

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response("User not found", 404)

    if target_user.id == current_user.id:
        return error_response("You cannot delete your own logged in account", 400)

    if target_user.role == "super_admin":
        super_admin_count = User.query.filter_by(role="super_admin").count()
        if super_admin_count <= 1:
            return error_response("Cannot delete the last remaining Super Admin", 400)

    email = target_user.email
    db.session.delete(target_user)
    db.session.commit()

    log_admin_action(current_user, "User Deleted", f"Permanently deleted user {email}")

    return success_response(message=f"User {email} permanently deleted successfully")


# =========================================================
# 2. ADMIN ACCOUNTS MANAGEMENT (SUPER ADMIN ONLY)
# =========================================================

@admin_bp.route("/accounts", methods=["GET"])
@jwt_required()
def get_admin_accounts():
    """List all admin accounts (Super Admin only)."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    admins = User.query.filter(User.role.in_(["admin", "super_admin"])).order_by(User.created_at.desc()).all()
    return success_response([a.to_dict() for a in admins])


@admin_bp.route("/accounts", methods=["POST"])
@jwt_required()
def create_admin_account():
    """Create a new admin account (Super Admin only)."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "admin")

    if not full_name or not email or not password:
        return error_response("full_name, email, and password are required", 400)

    if len(password) < 6:
        return error_response("Password must be at least 6 characters long", 400)

    if role not in ["admin", "super_admin"]:
        role = "admin"

    clean_email = email.lower().strip()
    if User.query.filter_by(email=clean_email).first():
        return error_response("An account with this email already exists", 409)

    new_admin = User(
        full_name=full_name.strip(),
        email=clean_email,
        phone=data.get("phone", "+94 77 000 0000"),
        role=role,
        status="active",
        district="Vavuniya",
        ds_division="Vavuniya Town",
        onboarding_completed=True,
    )
    new_admin.set_password(password)

    db.session.add(new_admin)
    db.session.commit()

    log_admin_action(current_user, "Admin Added", f"Created new {role} account for {clean_email}")

    return success_response(new_admin.to_dict(), message="Admin account created successfully", status_code=201)


@admin_bp.route("/accounts/<int:admin_id>", methods=["PUT"])
@jwt_required()
def update_admin_account(admin_id):
    """Edit an admin account details or role (Super Admin only)."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    target_admin = User.query.get(admin_id)
    if not target_admin or target_admin.role not in ["admin", "super_admin"]:
        return error_response("Admin account not found", 404)

    data = request.get_json(silent=True) or {}
    if "full_name" in data and data["full_name"]:
        target_admin.full_name = data["full_name"].strip()
    if "email" in data and data["email"]:
        clean_email = data["email"].lower().strip()
        if clean_email != target_admin.email and User.query.filter_by(email=clean_email).first():
            return error_response("Email already in use by another user", 409)
        target_admin.email = clean_email

    if "role" in data and data["role"] in ["admin", "super_admin"]:
        # Prevent demoting the last super admin
        if target_admin.role == "super_admin" and data["role"] == "admin":
            super_admin_count = User.query.filter_by(role="super_admin").count()
            if super_admin_count <= 1:
                return error_response("Cannot demote the last remaining Super Admin", 400)
        target_admin.role = data["role"]

    if "status" in data and data["status"] in ["active", "banned"]:
        if target_admin.id == current_user.id and data["status"] == "banned":
            return error_response("Cannot ban your own logged-in account", 400)
        target_admin.status = data["status"]

    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return error_response("Password must be at least 6 characters", 400)
        target_admin.set_password(data["password"])

    db.session.commit()

    log_admin_action(current_user, "Admin Updated", f"Updated details for admin {target_admin.email}")

    return success_response(target_admin.to_dict(), message="Admin account updated successfully")


@admin_bp.route("/accounts/<int:admin_id>", methods=["DELETE"])
@jwt_required()
def delete_admin_account(admin_id):
    """Delete an admin account (Super Admin only)."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    target_admin = User.query.get(admin_id)
    if not target_admin or target_admin.role not in ["admin", "super_admin"]:
        return error_response("Admin account not found", 404)

    if target_admin.id == current_user.id:
        return error_response("You cannot delete your currently logged-in Super Admin account", 400)

    if target_admin.role == "super_admin":
        super_admin_count = User.query.filter_by(role="super_admin").count()
        if super_admin_count <= 1:
            return error_response("Cannot delete the last remaining Super Admin account", 400)

    email = target_admin.email
    db.session.delete(target_admin)
    db.session.commit()

    log_admin_action(current_user, "Admin Deleted", f"Deleted admin account {email}")

    return success_response(message=f"Admin account {email} deleted successfully")


# =========================================================
# 3. ACTIVITY LOGS ENDPOINT
# =========================================================

@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
def get_admin_logs():
    """Retrieve audit activity logs for administrative actions."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = AdminActivityLog.query.order_by(AdminActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response({
        "items": [log.to_dict() for log in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })
