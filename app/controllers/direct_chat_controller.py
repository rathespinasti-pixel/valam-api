from flask import request

from app.extensions import db
from app.models.marketplace_models import DirectMessage, MarketNotification
from app.models.user import User
from app.utils.decorators import success_response, error_response, get_current_user


def get_conversations():
    """
    Get all chat threads for the logged-in user with their latest message and unread count.
    """
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    # Find all messages where user is sender or receiver
    messages = DirectMessage.query.filter(
        db.or_(DirectMessage.sender_id == user.id, DirectMessage.receiver_id == user.id)
    ).order_by(DirectMessage.created_at.desc()).all()

    threads = {}
    for msg in messages:
        partner_id = msg.receiver_id if msg.sender_id == user.id else msg.sender_id
        if partner_id not in threads:
            partner = User.query.get(partner_id)
            if not partner:
                continue

            unread_count = DirectMessage.query.filter_by(
                sender_id=partner_id, receiver_id=user.id, is_read=False
            ).count()

            threads[partner_id] = {
                "partner": {
                    "id": partner.id,
                    "full_name": partner.full_name,
                    "role": partner.role,
                    "district": partner.district,
                    "phone": partner.phone,
                },
                "last_message": msg.to_dict(),
                "unread_count": unread_count,
            }

    return success_response(list(threads.values()))


def get_messages(other_user_id):
    """
    Get message history between the logged-in user and another user.
    Automatically marks incoming messages as read.
    """
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    other = User.query.get(other_user_id)
    if not other:
        return error_response("User not found", 404)

    # Mark unread incoming messages as read
    DirectMessage.query.filter_by(
        sender_id=other_user_id, receiver_id=user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()

    messages = DirectMessage.query.filter(
        db.or_(
            db.and_(DirectMessage.sender_id == user.id, DirectMessage.receiver_id == other_user_id),
            db.and_(DirectMessage.sender_id == other_user_id, DirectMessage.receiver_id == user.id),
        )
    ).order_by(DirectMessage.created_at.asc()).all()

    return success_response({
        "partner": {
            "id": other.id,
            "full_name": other.full_name,
            "role": other.role,
            "district": other.district,
            "phone": other.phone,
        },
        "messages": [m.to_dict() for m in messages],
    })


def send_message():
    """
    Send a direct message to another user.
    """
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    message_text = (data.get("message") or "").strip()
    listing_id = data.get("listing_id")

    if not receiver_id or not message_text:
        return error_response("receiver_id and message are required", 400)

    if receiver_id == user.id:
        return error_response("You cannot send messages to yourself", 400)

    receiver = User.query.get(receiver_id)
    if not receiver:
        return error_response("Recipient not found", 404)

    msg = DirectMessage(
        sender_id=user.id,
        receiver_id=receiver.id,
        listing_id=listing_id,
        message=message_text,
        is_read=False,
    )
    db.session.add(msg)

    # Create notification for recipient
    notif = MarketNotification(
        user_id=receiver.id,
        sender_id=user.id,
        title=f"💬 New message from {user.full_name}",
        message=message_text[:120] + ("..." if len(message_text) > 120 else ""),
        category="chat",
        link_url=f"/chat?partner_id={user.id}",
        is_read=False,
    )
    db.session.add(notif)

    db.session.commit()

    return success_response(msg.to_dict(), message="Message sent successfully", status_code=201)
