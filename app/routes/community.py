from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.community_controller import (
    get_posts,
    get_post_detail,
    create_post,
    add_comment,
    delete_post,
)

community_bp = Blueprint("community", __name__)

community_bp.add_url_rule("/posts", view_func=get_posts, methods=["GET"])
community_bp.add_url_rule("/posts/<int:post_id>", view_func=get_post_detail, methods=["GET"])
community_bp.add_url_rule("/posts", view_func=jwt_required()(create_post), methods=["POST"])
community_bp.add_url_rule("/posts/<int:post_id>/comments", view_func=jwt_required()(add_comment), methods=["POST"])
community_bp.add_url_rule("/posts/<int:post_id>", view_func=jwt_required()(delete_post), methods=["DELETE"])
