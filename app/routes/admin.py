import io
import csv
from datetime import datetime, timedelta
from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.crop import Crop
from app.models.crop_guide import CropGuide
from app.models.disease_diagnosis import DiseaseDiagnosis
from app.models.disease_catalog import DiseaseCatalog
from app.models.system_notification import SystemNotification
from app.models.user_feedback import UserFeedback
from app.models.faq_item import FAQItem
from app.models.system_setting import SystemSetting
from app.models.admin_activity_log import AdminActivityLog
from app.utils.decorators import success_response, error_response, get_current_user

admin_bp = Blueprint("admin", __name__)


def log_admin_action(admin, action: str, details: str):
    """Record audit trail of administrative operations."""
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
        print(f"Error logging admin action: {e}")


# =========================================================
# 1. ADMIN DASHBOARD OVERVIEW REAL-TIME STATS
# =========================================================

@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_admin_stats():
    """Get real-time statistics for dashboard overview."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    month_start = datetime(now.year, now.month, 1)

    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter(User.status == "active").count()
    banned_users = User.query.filter(User.status == "banned").count()
    inactive_users = max(0, total_users - active_users - banned_users)

    farmer_count = User.query.filter(User.farming_category.ilike("Farmer")).count()
    home_gardener_count = User.query.filter(User.farming_category.ilike("Home Gardener")).count()
    terrace_gardener_count = User.query.filter(User.farming_category.ilike("Terrace Gardener")).count()
    beginner_count = User.query.filter(User.farming_category.ilike("Beginner")).count()

    new_today = User.query.filter(User.created_at >= today_start).count()
    new_month = User.query.filter(User.created_at >= month_start).count()

    # Crop statistics
    total_supported_crops = CropGuide.query.count()
    total_active_crop_records = Crop.query.count()

    most_cultivated_row = db.session.query(
        Crop.crop_name, func.count(Crop.id).label("cnt")
    ).group_by(Crop.crop_name).order_by(func.count(Crop.id).desc()).first()

    most_cultivated_crop = most_cultivated_row[0] if most_cultivated_row else "Tomato"

    recently_added_crops = [
        c.crop_name for c in CropGuide.query.order_by(CropGuide.created_at.desc()).limit(5).all()
    ]

    # Disease statistics
    total_disease_reports = DiseaseDiagnosis.query.count()
    pending_disease_reports = DiseaseDiagnosis.query.filter(DiseaseDiagnosis.status == "pending").count()
    resolved_disease_reports = DiseaseDiagnosis.query.filter(DiseaseDiagnosis.status == "resolved").count()

    # System statistics
    total_admins = User.query.filter(User.role.in_(["admin", "super_admin"])).count()
    total_notifications = SystemNotification.query.count()

    return success_response({
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "banned": banned_users,
            "farmers": farmer_count,
            "home_gardeners": home_gardener_count,
            "terrace_gardeners": terrace_gardener_count,
            "beginners": beginner_count,
            "new_today": new_today,
            "new_this_month": new_month,
        },
        "crops": {
            "total_supported": total_supported_crops,
            "total_active_records": total_active_crop_records,
            "most_cultivated": most_cultivated_crop,
            "recently_added": recently_added_crops,
        },
        "diseases": {
            "total": total_disease_reports,
            "pending": pending_disease_reports,
            "resolved": resolved_disease_reports,
        },
        "system": {
            "total_admins": total_admins,
            "online_users": max(1, active_users // 3),
            "active_sessions": active_users,
            "total_notifications_sent": total_notifications,
        }
    })


# =========================================================
# 2. USER MANAGEMENT ENDPOINTS
# =========================================================

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def get_admin_users():
    """List users with search, filtering & pagination."""
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
        query = query.filter((User.full_name.ilike(s)) | (User.email.ilike(s)) | (User.phone.ilike(s)))

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


@admin_bp.route("/users", methods=["POST"])
@jwt_required()
def create_user():
    """Create a new farmer user account."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required to create users", 403)

    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone", "+94 77 000 0000")

    if not full_name or not email or not password:
        return error_response("full_name, email, and password are required", 400)

    clean_email = email.lower().strip()
    if User.query.filter_by(email=clean_email).first():
        return error_response("User with this email already exists", 409)

    user = User(
        full_name=full_name.strip(),
        email=clean_email,
        phone=phone,
        farming_category=data.get("farming_category", "Farmer"),
        district=data.get("district", "Vavuniya"),
        ds_division=data.get("ds_division", "Vavuniya Town"),
        role="farmer",
        status="active",
        onboarding_completed=True,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log_admin_action(current_user, "User Created", f"Created farmer account for {clean_email}")
    return success_response(user.to_dict(), message="User created successfully", status_code=201)


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_admin_user_profile(user_id):
    """Update user profile details."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required to update users", 403)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    fields = (
        "full_name", "email", "phone", "farming_category", "farmer_type",
        "district", "ds_division", "gn_division", "land_size", "land_size_unit",
        "irrigation_preference", "fertilizer_preference", "preferred_language",
        "status", "ban_reason"
    )
    for f in fields:
        if f in data:
            setattr(user, f, data[f])

    if "password" in data and data["password"]:
        if len(data["password"]) >= 6:
            user.set_password(data["password"])

    db.session.commit()
    log_admin_action(current_user, "User Updated", f"Updated user profile for {user.email}")
    return success_response(user.to_dict(), message="User profile updated successfully")


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["PUT"])
@jwt_required()
def reset_user_password(user_id):
    """Reset password for a user account."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required to reset user passwords", 403)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    new_password = data.get("password")
    if not new_password or len(new_password) < 6:
        return error_response("Password must be at least 6 characters long", 400)

    user.set_password(new_password)
    db.session.commit()

    log_admin_action(current_user, "Password Reset", f"Reset password for user {user.email}")
    return success_response(message=f"Password reset successfully for {user.email}")


@admin_bp.route("/users/<int:user_id>/ban", methods=["PUT"])
@jwt_required()
def ban_unban_user(user_id):
    """Toggle Ban / Unban status for a user with reason."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required to ban or unban users", 403)

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response("User not found", 404)

    if target_user.role in ["admin", "super_admin"] and current_user.role != "super_admin":
        return error_response("Admins cannot ban other admin accounts", 403)

    if target_user.role == "super_admin":
        return error_response("Cannot ban Super Admin account", 400)

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ["active", "banned"]:
        new_status = "banned" if target_user.status == "active" else "active"

    reason = data.get("reason", "").strip()
    target_user.status = new_status
    if new_status == "banned":
        target_user.ban_reason = reason if reason else "Account suspended for violating platform policies."
    else:
        target_user.ban_reason = None

    db.session.commit()

    action_label = "User Banned" if new_status == "banned" else "User Unbanned"
    details = f"Changed status of {target_user.email} to {new_status}"
    if target_user.ban_reason:
        details += f" (Reason: {target_user.ban_reason})"
    log_admin_action(current_user, action_label, details)

    return success_response(target_user.to_dict(), message=f"User status updated to {new_status}")


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_admin_user(user_id):
    """Permanently delete a user account."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required to delete users", 403)

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response("User not found", 404)

    if target_user.id == current_user.id:
        return error_response("You cannot delete your own logged in account", 400)

    if target_user.role in ["admin", "super_admin"] and current_user.role != "super_admin":
        return error_response("Admins cannot delete other admin accounts", 403)

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
# 3. DISEASE CATALOG & FARMER REPORTS MANAGEMENT
# =========================================================

@admin_bp.route("/diseases", methods=["GET"])
@jwt_required()
def get_disease_catalog():
    """List disease knowledge base catalog entries."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    diseases = DiseaseCatalog.query.order_by(DiseaseCatalog.created_at.desc()).all()
    return success_response([d.to_dict() for d in diseases])


@admin_bp.route("/diseases", methods=["POST"])
@jwt_required()
def create_disease_entry():
    """Add a new disease entry to catalog."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    data = request.get_json(silent=True) or {}
    name = data.get("disease_name")
    crop = data.get("crop_name")
    symptoms = data.get("symptoms")

    if not name or not crop or not symptoms:
        return error_response("disease_name, crop_name, and symptoms are required", 400)

    entry = DiseaseCatalog(
        disease_name=name,
        crop_name=crop,
        symptoms=symptoms,
        causes=data.get("causes"),
        organic_treatment=data.get("organic_treatment"),
        chemical_treatment=data.get("chemical_treatment"),
        prevention_tips=data.get("prevention_tips"),
        image_url=data.get("image_url"),
    )
    db.session.add(entry)
    db.session.commit()

    log_admin_action(current_user, "Disease Added", f"Added disease entry {name} for {crop}")
    return success_response(entry.to_dict(), message="Disease catalog entry created successfully", status_code=201)


@admin_bp.route("/diseases/<int:disease_id>", methods=["PUT"])
@jwt_required()
def update_disease_entry(disease_id):
    """Edit disease catalog entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    entry = DiseaseCatalog.query.get(disease_id)
    if not entry:
        return error_response("Disease entry not found", 404)

    data = request.get_json(silent=True) or {}
    fields = ("disease_name", "crop_name", "symptoms", "causes", "organic_treatment", "chemical_treatment", "prevention_tips", "image_url")
    for f in fields:
        if f in data:
            setattr(entry, f, data[f])

    db.session.commit()
    log_admin_action(current_user, "Disease Updated", f"Updated disease entry {entry.disease_name}")
    return success_response(entry.to_dict(), message="Disease entry updated successfully")


@admin_bp.route("/diseases/<int:disease_id>", methods=["DELETE"])
@jwt_required()
def delete_disease_entry(disease_id):
    """Delete disease catalog entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    entry = DiseaseCatalog.query.get(disease_id)
    if not entry:
        return error_response("Disease entry not found", 404)

    name = entry.disease_name
    db.session.delete(entry)
    db.session.commit()

    log_admin_action(current_user, "Disease Deleted", f"Deleted disease entry {name}")
    return success_response(message=f"Disease entry {name} deleted successfully")


@admin_bp.route("/disease-reports", methods=["GET"])
@jwt_required()
def get_farmer_disease_reports():
    """List farmer-submitted AI disease diagnosis reports."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    reports = DiseaseDiagnosis.query.order_by(DiseaseDiagnosis.created_at.desc()).all()
    return success_response([r.to_dict() for r in reports])


@admin_bp.route("/disease-reports/<int:report_id>", methods=["PUT"])
@jwt_required()
def update_farmer_disease_report(report_id):
    """Approve, reject, or update recommendation on a farmer disease report."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    report = DiseaseDiagnosis.query.get(report_id)
    if not report:
        return error_response("Report not found", 404)

    data = request.get_json(silent=True) or {}
    if "status" in data:
        report.status = data["status"]
    if "recommendations" in data:
        report.recommendations = data["recommendations"]

    db.session.commit()
    log_admin_action(current_user, "Disease Report Updated", f"Updated report #{report_id} status to {report.status}")
    return success_response(report.to_dict(), message="Disease report updated successfully")


# =========================================================
# 4. NOTIFICATION MANAGEMENT ENDPOINTS
# =========================================================

@admin_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_system_notifications():
    """List system broadcast notifications."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    notes = SystemNotification.query.order_by(SystemNotification.created_at.desc()).all()
    return success_response([n.to_dict() for n in notes])


@admin_bp.route("/notifications", methods=["POST"])
@jwt_required()
def create_system_notification():
    """Create and broadcast a notification."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    data = request.get_json(silent=True) or {}
    title = data.get("title")
    message = data.get("message")

    if not title or not message:
        return error_response("title and message are required", 400)

    note = SystemNotification(
        title=title,
        message=message,
        category=data.get("category", "Alert"),
        target_type=data.get("target_type", "All Users"),
        target_value=data.get("target_value"),
        status="sent",
    )
    db.session.add(note)
    db.session.commit()

    log_admin_action(current_user, "Notification Sent", f"Broadcast notification '{title}' to {note.target_type}")
    return success_response(note.to_dict(), message="Notification created & sent successfully", status_code=201)


@admin_bp.route("/notifications/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_system_notification(note_id):
    """Delete a system notification record."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    note = SystemNotification.query.get(note_id)
    if not note:
        return error_response("Notification not found", 404)

    title = note.title
    db.session.delete(note)
    db.session.commit()

    log_admin_action(current_user, "Notification Deleted", f"Deleted notification '{title}'")
    return success_response(message=f"Notification '{title}' deleted successfully")


# =========================================================
# 5. USER FEEDBACK MANAGEMENT
# =========================================================

@admin_bp.route("/feedback", methods=["GET"])
@jwt_required()
def get_user_feedback():
    """List user feedback messages."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    items = UserFeedback.query.order_by(UserFeedback.created_at.desc()).all()
    return success_response([i.to_dict() for i in items])


@admin_bp.route("/feedback/<int:fb_id>", methods=["PUT"])
@jwt_required()
def reply_user_feedback(fb_id):
    """Reply to user feedback or mark resolved."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    fb = UserFeedback.query.get(fb_id)
    if not fb:
        return error_response("Feedback item not found", 404)

    data = request.get_json(silent=True) or {}
    if "admin_reply" in data:
        fb.admin_reply = data["admin_reply"]
        fb.status = "replied"
    if "status" in data:
        fb.status = data["status"]

    db.session.commit()
    log_admin_action(current_user, "Feedback Replied", f"Updated feedback #{fb_id} status to {fb.status}")
    return success_response(fb.to_dict(), message="Feedback updated successfully")


@admin_bp.route("/feedback/<int:fb_id>", methods=["DELETE"])
@jwt_required()
def delete_user_feedback(fb_id):
    """Delete user feedback entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    fb = UserFeedback.query.get(fb_id)
    if not fb:
        return error_response("Feedback item not found", 404)

    db.session.delete(fb)
    db.session.commit()
    return success_response(message="Feedback deleted successfully")


# =========================================================
# 6. FAQ MANAGEMENT
# =========================================================

@admin_bp.route("/faqs", methods=["GET"])
def get_public_faqs():
    """List all public published FAQs."""
    faqs = FAQItem.query.filter_by(is_published=True).order_by(FAQItem.order_num.asc()).all()
    return success_response([f.to_dict() for f in faqs])


@admin_bp.route("/faqs/all", methods=["GET"])
@jwt_required()
def get_all_admin_faqs():
    """List all FAQs for administrative editing."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    faqs = FAQItem.query.order_by(FAQItem.order_num.asc()).all()
    return success_response([f.to_dict() for f in faqs])


@admin_bp.route("/faqs", methods=["POST"])
@jwt_required()
def create_faq_item():
    """Create a new FAQ entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    data = request.get_json(silent=True) or {}
    q = data.get("question")
    a = data.get("answer")
    if not q or not a:
        return error_response("question and answer are required", 400)

    faq = FAQItem(
        question=q,
        answer=a,
        category=data.get("category", "General"),
        is_published=data.get("is_published", True),
        order_num=data.get("order_num", 1),
    )
    db.session.add(faq)
    db.session.commit()

    log_admin_action(current_user, "FAQ Added", f"Created FAQ '{q}'")
    return success_response(faq.to_dict(), message="FAQ created successfully", status_code=201)


@admin_bp.route("/faqs/<int:faq_id>", methods=["PUT"])
@jwt_required()
def update_faq_item(faq_id):
    """Edit FAQ entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    faq = FAQItem.query.get(faq_id)
    if not faq:
        return error_response("FAQ item not found", 404)

    data = request.get_json(silent=True) or {}
    fields = ("question", "answer", "category", "is_published", "order_num")
    for f in fields:
        if f in data:
            setattr(faq, f, data[f])

    db.session.commit()
    log_admin_action(current_user, "FAQ Updated", f"Updated FAQ #{faq_id}")
    return success_response(faq.to_dict(), message="FAQ updated successfully")


@admin_bp.route("/faqs/<int:faq_id>", methods=["DELETE"])
@jwt_required()
def delete_faq_item(faq_id):
    """Delete FAQ entry."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    faq = FAQItem.query.get(faq_id)
    if not faq:
        return error_response("FAQ item not found", 404)

    db.session.delete(faq)
    db.session.commit()
    return success_response(message="FAQ deleted successfully")


# =========================================================
# 7. SYSTEM SETTINGS MANAGEMENT (SUPER ADMIN ONLY)
# =========================================================

@admin_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_system_settings():
    """Get key-value system settings."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    settings = SystemSetting.query.all()
    res = {s.setting_key: s.setting_value for s in settings}
    return success_response(res)


@admin_bp.route("/settings", methods=["PUT"])
@jwt_required()
def update_system_settings():
    """Update system settings (Super Admin only)."""
    current_user = get_current_user()
    if not current_user or current_user.role != "super_admin":
        return error_response("Super Admin authorization required", 403)

    data = request.get_json(silent=True) or {}
    for key, value in data.items():
        s = SystemSetting.query.filter_by(setting_key=key).first()
        if not s:
            s = SystemSetting(setting_key=key, setting_value=str(value))
            db.session.add(s)
        else:
            s.setting_value = str(value)

    db.session.commit()
    log_admin_action(current_user, "Settings Updated", "Updated platform system configuration settings")
    return success_response(message="System settings updated successfully")


# =========================================================
# 8. CSV DATA EXPORT ENDPOINTS
# =========================================================

@admin_bp.route("/export/users", methods=["GET"])
@jwt_required()
def export_users_csv():
    """Export User Directory to CSV."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    users = User.query.order_by(User.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Full Name", "Email", "Phone", "Category", "District", "Status", "Role", "Registration Date"])

    for u in users:
        writer.writerow([
            u.id, u.full_name, u.email, u.phone or "", u.farming_category or "", u.district or "", u.status or "active", u.role,
            u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=valam_users_export.csv"}
    )


@admin_bp.route("/export/crops", methods=["GET"])
@jwt_required()
def export_crops_csv():
    """Export Crop Database to CSV."""
    current_user = get_current_user()
    if not current_user or current_user.role not in ["admin", "super_admin"]:
        return error_response("Admin authorization required", 403)

    guides = CropGuide.query.order_by(CropGuide.crop_name.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Crop Name", "Variety", "Recommended Season", "Water Requirements", "Fertilizer Guidance"])

    for g in guides:
        writer.writerow([g.id, g.crop_name, g.variety or "", g.recommended_season or "", g.water_requirements or "", g.fertilizer_guidance or ""])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=valam_crops_export.csv"}
    )


# =========================================================
# 9. ADMIN ACCOUNTS & ACTIVITY LOGS (SUPER ADMIN ONLY)
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


@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
def get_admin_logs():
    """Retrieve audit activity logs."""
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
