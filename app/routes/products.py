from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.products_controller import (
    get_products,
    get_product_detail,
    get_products_by_category,
    add_product,
    update_product,
    delete_product,
)

products_bp = Blueprint("products", __name__)

products_bp.add_url_rule("", view_func=get_products, methods=["GET"])
products_bp.add_url_rule("/<int:product_id>", view_func=get_product_detail, methods=["GET"])
products_bp.add_url_rule("/category/<string:name>", view_func=get_products_by_category, methods=["GET"])
products_bp.add_url_rule("", view_func=jwt_required()(add_product), methods=["POST"])
products_bp.add_url_rule("/<int:product_id>", view_func=jwt_required()(update_product), methods=["PUT"])
products_bp.add_url_rule("/<int:product_id>", view_func=jwt_required()(delete_product), methods=["DELETE"])
