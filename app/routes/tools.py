from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.tools_controller import (
    get_tools,
    get_tool_detail,
    create_tool_listing,
    update_tool_listing,
    delete_tool_listing,
)

tools_bp = Blueprint("tools", __name__)

tools_bp.add_url_rule("", view_func=get_tools, methods=["GET"])
tools_bp.add_url_rule("/<int:tool_id>", view_func=get_tool_detail, methods=["GET"])
tools_bp.add_url_rule("", view_func=jwt_required()(create_tool_listing), methods=["POST"])
tools_bp.add_url_rule("/<int:tool_id>", view_func=jwt_required()(update_tool_listing), methods=["PUT"])
tools_bp.add_url_rule("/<int:tool_id>", view_func=jwt_required()(delete_tool_listing), methods=["DELETE"])
