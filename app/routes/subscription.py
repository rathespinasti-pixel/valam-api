from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.subscription_controller import (
    feature_access,
    get_subscription,
)

subscription_bp = Blueprint('subscription', __name__)

subscription_bp.add_url_rule('/feature-access', view_func=jwt_required()(feature_access), methods=['GET'])
subscription_bp.add_url_rule('', view_func=jwt_required()(get_subscription), methods=['GET'])
