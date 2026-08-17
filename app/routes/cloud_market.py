from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.cloud_market_controller import (
    get_listings,
    get_listing_detail,
    create_listing,
    update_listing,
    delete_listing,
    create_bargain_offer,
    get_my_offers,
    get_incoming_offers,
    respond_to_offer,
    accept_counter_offer,
)

cloud_market_bp = Blueprint("cloud_market", __name__)

# Produce listings
cloud_market_bp.add_url_rule("/listings", view_func=get_listings, methods=["GET"])
cloud_market_bp.add_url_rule("/listings/<int:listing_id>", view_func=get_listing_detail, methods=["GET"])
cloud_market_bp.add_url_rule("/listings", view_func=jwt_required()(create_listing), methods=["POST"])
cloud_market_bp.add_url_rule("/listings/<int:listing_id>", view_func=jwt_required()(update_listing), methods=["PUT"])
cloud_market_bp.add_url_rule("/listings/<int:listing_id>", view_func=jwt_required()(delete_listing), methods=["DELETE"])

# Bargaining / offers
cloud_market_bp.add_url_rule("/listings/<int:listing_id>/offers", view_func=jwt_required()(create_bargain_offer), methods=["POST"])
cloud_market_bp.add_url_rule("/offers/my-offers", view_func=jwt_required()(get_my_offers), methods=["GET"])
cloud_market_bp.add_url_rule("/offers/incoming", view_func=jwt_required()(get_incoming_offers), methods=["GET"])
cloud_market_bp.add_url_rule("/offers/<int:offer_id>/respond", view_func=jwt_required()(respond_to_offer), methods=["PUT"])
cloud_market_bp.add_url_rule("/offers/<int:offer_id>/accept-counter", view_func=jwt_required()(accept_counter_offer), methods=["PUT"])
