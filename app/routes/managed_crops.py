from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.managed_crops_controller import (
    list_admin_crops,
    create_crop,
    crop_detail,
    add_lifecycle_stage,
    edit_lifecycle_stage,
    change_status,
    ai_suggestions,
    generate_stage_image,
    approve_stage_image,
    public_crops,
    public_crop,
)

managed_crops_bp = Blueprint("managed_crops", __name__)
public_catalogue_bp = Blueprint("public_crop_catalogue", __name__)

# Admin-protected managed crops routes
managed_crops_bp.add_url_rule("", view_func=jwt_required()(list_admin_crops), methods=["GET"])
managed_crops_bp.add_url_rule("", view_func=jwt_required()(create_crop), methods=["POST"])
managed_crops_bp.add_url_rule("/<int:crop_id>", view_func=jwt_required()(crop_detail), methods=["GET", "PUT", "DELETE"])
managed_crops_bp.add_url_rule("/<int:crop_id>/lifecycle", view_func=jwt_required()(add_lifecycle_stage), methods=["POST"])
managed_crops_bp.add_url_rule("/<int:crop_id>/lifecycle/<int:stage_id>", view_func=jwt_required()(edit_lifecycle_stage), methods=["PUT", "DELETE"])
managed_crops_bp.add_url_rule("/<int:crop_id>/<action>", view_func=jwt_required()(change_status), methods=["POST"])
managed_crops_bp.add_url_rule("/<int:crop_id>/ai-suggestions", view_func=jwt_required()(ai_suggestions), methods=["POST"])
managed_crops_bp.add_url_rule("/<int:crop_id>/lifecycle/<int:stage_id>/generate-image", view_func=jwt_required()(generate_stage_image), methods=["POST"])
managed_crops_bp.add_url_rule("/<int:crop_id>/lifecycle/<int:stage_id>/approve-image", view_func=jwt_required()(approve_stage_image), methods=["POST"])

# Public catalogue routes
public_catalogue_bp.add_url_rule("", view_func=public_crops, methods=["GET"])
public_catalogue_bp.add_url_rule("/<int:crop_id>", view_func=public_crop, methods=["GET"])
