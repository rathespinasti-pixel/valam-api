from flask import Blueprint

from app.controllers.solar_controller import (
    get_guides,
    get_guide_detail,
)

solar_bp = Blueprint("solar", __name__)

solar_bp.add_url_rule("/guides", view_func=get_guides, methods=["GET"])
solar_bp.add_url_rule("/guides/<int:guide_id>", view_func=get_guide_detail, methods=["GET"])
