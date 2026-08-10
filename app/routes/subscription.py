from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.subscription_service import SubscriptionService

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/feature-access', methods=['GET'])
@jwt_required()
def feature_access():
    """Return feature access flags based on the user's subscription level."""
    user_id = get_jwt_identity()
    # Determine access flags
    access = {
        'marketplace': SubscriptionService.can_access_marketplace(user_id)
    }
    return jsonify({'success': True, 'features': access}), 200

@subscription_bp.route('', methods=['GET'])
@jwt_required()
def get_subscription():
    """Return the current user's subscription details."""
    user_id = get_jwt_identity()
    sub = SubscriptionService.get_subscription(user_id)
    if not sub:
        return jsonify({'success': False, 'message': 'No subscription found'}), 404
    return jsonify({'success': True, 'subscription': sub.to_dict()}), 200
