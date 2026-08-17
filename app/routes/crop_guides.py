from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.crop_guides_controller import (
    get_crop_guides,
    get_crop_guide_detail,
    create_crop_guide,
    update_crop_guide,
    delete_crop_guide,
    suggest_agronomy,
)

crop_guides_bp = Blueprint("crop_guides", __name__)

crop_guides_bp.add_url_rule("", view_func=get_crop_guides, methods=["GET"])
crop_guides_bp.add_url_rule("/<int:guide_id>", view_func=get_crop_guide_detail, methods=["GET"])
crop_guides_bp.add_url_rule("", view_func=jwt_required()(create_crop_guide), methods=["POST"])
crop_guides_bp.add_url_rule("/<int:guide_id>", view_func=jwt_required()(update_crop_guide), methods=["PUT"])
crop_guides_bp.add_url_rule("/<int:guide_id>", view_func=jwt_required()(delete_crop_guide), methods=["DELETE"])
crop_guides_bp.add_url_rule("/suggest-agronomy", view_func=jwt_required()(suggest_agronomy), methods=["POST"])
