from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.admin_controller import (
    # Stats
    get_admin_stats,
    # User management
    get_admin_users,
    create_user,
    update_admin_user_profile,
    reset_user_password,
    ban_unban_user,
    delete_admin_user,
    # Disease catalog & reports
    get_disease_catalog,
    create_disease_entry,
    update_disease_entry,
    delete_disease_entry,
    get_farmer_disease_reports,
    update_farmer_disease_report,
    # Notifications
    get_system_notifications,
    create_system_notification,
    delete_system_notification,
    # Feedback
    get_user_feedback,
    reply_user_feedback,
    delete_user_feedback,
    # FAQs
    get_public_faqs,
    get_all_admin_faqs,
    create_faq_item,
    update_faq_item,
    delete_faq_item,
    # Settings
    get_system_settings,
    update_system_settings,
    # CSV exports
    export_users_csv,
    export_crops_csv,
    # Lifecycle image
    generate_crop_stage_image,
    # Admin accounts & logs
    get_admin_accounts,
    create_admin_account,
    update_admin_account,
    delete_admin_account,
    get_admin_logs,
)

admin_bp = Blueprint("admin", __name__)

# 1. Dashboard stats
admin_bp.add_url_rule("/stats", view_func=jwt_required()(get_admin_stats), methods=["GET"])

# 2. User management
admin_bp.add_url_rule("/users", view_func=jwt_required()(get_admin_users), methods=["GET"])
admin_bp.add_url_rule("/users", view_func=jwt_required()(create_user), methods=["POST"])
admin_bp.add_url_rule("/users/<int:user_id>", view_func=jwt_required()(update_admin_user_profile), methods=["PUT"])
admin_bp.add_url_rule("/users/<int:user_id>/reset-password", view_func=jwt_required()(reset_user_password), methods=["PUT"])
admin_bp.add_url_rule("/users/<int:user_id>/ban", view_func=jwt_required()(ban_unban_user), methods=["PUT"])
admin_bp.add_url_rule("/users/<int:user_id>", view_func=jwt_required()(delete_admin_user), methods=["DELETE"])

# 3. Disease catalog & farmer reports
admin_bp.add_url_rule("/diseases", view_func=jwt_required()(get_disease_catalog), methods=["GET"])
admin_bp.add_url_rule("/diseases", view_func=jwt_required()(create_disease_entry), methods=["POST"])
admin_bp.add_url_rule("/diseases/<int:disease_id>", view_func=jwt_required()(update_disease_entry), methods=["PUT"])
admin_bp.add_url_rule("/diseases/<int:disease_id>", view_func=jwt_required()(delete_disease_entry), methods=["DELETE"])
admin_bp.add_url_rule("/disease-reports", view_func=jwt_required()(get_farmer_disease_reports), methods=["GET"])
admin_bp.add_url_rule("/disease-reports/<int:report_id>", view_func=jwt_required()(update_farmer_disease_report), methods=["PUT"])

# 4. System notifications
admin_bp.add_url_rule("/notifications", view_func=jwt_required()(get_system_notifications), methods=["GET"])
admin_bp.add_url_rule("/notifications", view_func=jwt_required()(create_system_notification), methods=["POST"])
admin_bp.add_url_rule("/notifications/<int:note_id>", view_func=jwt_required()(delete_system_notification), methods=["DELETE"])

# 5. User feedback
admin_bp.add_url_rule("/feedback", view_func=jwt_required()(get_user_feedback), methods=["GET"])
admin_bp.add_url_rule("/feedback/<int:fb_id>", view_func=jwt_required()(reply_user_feedback), methods=["PUT"])
admin_bp.add_url_rule("/feedback/<int:fb_id>", view_func=jwt_required()(delete_user_feedback), methods=["DELETE"])

# 6. FAQs
admin_bp.add_url_rule("/faqs", view_func=get_public_faqs, methods=["GET"])
admin_bp.add_url_rule("/faqs/all", view_func=jwt_required()(get_all_admin_faqs), methods=["GET"])
admin_bp.add_url_rule("/faqs", view_func=jwt_required()(create_faq_item), methods=["POST"])
admin_bp.add_url_rule("/faqs/<int:faq_id>", view_func=jwt_required()(update_faq_item), methods=["PUT"])
admin_bp.add_url_rule("/faqs/<int:faq_id>", view_func=jwt_required()(delete_faq_item), methods=["DELETE"])

# 7. System settings (Super Admin only)
admin_bp.add_url_rule("/settings", view_func=jwt_required()(get_system_settings), methods=["GET"])
admin_bp.add_url_rule("/settings", view_func=jwt_required()(update_system_settings), methods=["PUT"])

# 8. CSV exports
admin_bp.add_url_rule("/export/users", view_func=jwt_required()(export_users_csv), methods=["GET"])
admin_bp.add_url_rule("/export/crops", view_func=jwt_required()(export_crops_csv), methods=["GET"])

# Lifecycle image generation (admin)
admin_bp.add_url_rule("/crops/generate-stage-image", view_func=jwt_required()(generate_crop_stage_image), methods=["POST"])

# 9. Admin accounts & activity logs (Super Admin only)
admin_bp.add_url_rule("/accounts", view_func=jwt_required()(get_admin_accounts), methods=["GET"])
admin_bp.add_url_rule("/accounts", view_func=jwt_required()(create_admin_account), methods=["POST"])
admin_bp.add_url_rule("/accounts/<int:admin_id>", view_func=jwt_required()(update_admin_account), methods=["PUT"])
admin_bp.add_url_rule("/accounts/<int:admin_id>", view_func=jwt_required()(delete_admin_account), methods=["DELETE"])
admin_bp.add_url_rule("/logs", view_func=jwt_required()(get_admin_logs), methods=["GET"])
