from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.marketplace_controller import (
    list_items,
    create_item,
)

marketplace_bp = Blueprint('marketplace', __name__)

marketplace_bp.add_url_rule('/items', view_func=jwt_required()(list_items), methods=['GET'])
marketplace_bp.add_url_rule('/items', view_func=jwt_required()(create_item), methods=['POST'])
