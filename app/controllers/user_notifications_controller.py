from flask import request

from app.extensions import db
from app.models.marketplace_models import MarketNotification
from app.utils.decorators import success_response, error_response, get_current_user


def get_user_notifications():
    """
    Get notifications for the logged-in user.
    """
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    limit = request.args.get("limit", 30, type=int)
    notifications = (
        MarketNotification.query.filter_by(user_id=user.id)
        .order_by(MarketNotification.created_at.desc())
        .limit(limit)
        .all()
    )

    unread_count = MarketNotification.query.filter_by(user_id=user.id, is_read=False).count()

    return success_response({
        "items": [n.to_dict() for n in notifications],
        "unread_count": unread_count,
    })


def mark_notification_read(notif_id):
    """Mark a notification as read."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    notif = MarketNotification.query.get(notif_id)
    if not notif or notif.user_id != user.id:
        return error_response("Notification not found", 404)

    notif.is_read = True
    db.session.commit()
    return success_response(notif.to_dict(), message="Notification marked as read")


def mark_all_notifications_read():
    """Mark all notifications for logged-in user as read."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    MarketNotification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return success_response(message="All notifications marked as read")
