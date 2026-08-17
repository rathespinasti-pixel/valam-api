from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.crops_controller import (
    get_crops,
    add_crop,
    update_crop,
    delete_crop,
    get_plant_info,
    get_lifecycle_image,
)

crops_bp = Blueprint("crops", __name__)

crops_bp.add_url_rule("", view_func=jwt_required()(get_crops), methods=["GET"])
crops_bp.add_url_rule("", view_func=jwt_required()(add_crop), methods=["POST"])
crops_bp.add_url_rule("/<int:crop_id>", view_func=jwt_required()(update_crop), methods=["PUT"])
crops_bp.add_url_rule("/<int:crop_id>", view_func=jwt_required()(delete_crop), methods=["DELETE"])
crops_bp.add_url_rule("/plant-info", view_func=get_plant_info, methods=["GET"])
crops_bp.add_url_rule("/lifecycle-image", view_func=jwt_required()(get_lifecycle_image), methods=["POST"])
