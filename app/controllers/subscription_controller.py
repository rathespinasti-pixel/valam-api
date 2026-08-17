from flask import jsonify

from app.services.subscription_service import SubscriptionService


def feature_access():
    """Return feature access flags based on the user's subscription level."""
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    # Determine access flags
    access = {
        'marketplace': SubscriptionService.can_access_marketplace(user_id)
    }
    return jsonify({'success': True, 'features': access}), 200


def get_subscription():
    """Return the current user's subscription details."""
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    sub = SubscriptionService.get_subscription(user_id)
    if not sub:
        return jsonify({'success': False, 'message': 'No subscription found'}), 404
    return jsonify({'success': True, 'subscription': sub.to_dict()}), 200
