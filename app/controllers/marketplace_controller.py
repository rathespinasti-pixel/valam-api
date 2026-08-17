from flask import jsonify, request

from app.services.subscription_service import SubscriptionService
from app.models.marketplace_item import MarketplaceItem
from app.extensions import db


def list_items():
    """Return marketplace items visible to the current user.
    Only PRO users can see items; others receive empty list.
    """
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    if not SubscriptionService.can_access_marketplace(user_id):
        return jsonify({'success': True, 'items': []}), 200
    items = MarketplaceItem.query.all()
    return jsonify({'success': True, 'items': [item.to_dict() for item in items]}), 200


def create_item():
    """Create a new marketplace item. Only PRO users are allowed.
    Expected JSON payload: {"name": str, "description": str, "price": float}
    """
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    if not SubscriptionService.can_access_marketplace(user_id):
        return jsonify({'success': False, 'message': 'Marketplace access denied'}), 403
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    if not name or price is None:
        return jsonify({'success': False, 'message': 'Invalid payload'}), 400
    item = MarketplaceItem(name=name, description=description, price=price)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()}), 201
