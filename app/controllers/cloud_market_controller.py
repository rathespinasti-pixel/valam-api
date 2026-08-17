from flask import request

from app.extensions import db
from app.models.marketplace_models import ProduceListing, BargainOffer, MarketNotification
from app.models.user import User
from app.utils.decorators import success_response, error_response, get_current_user


def get_listings():
    """
    Get active produce listings with optional filters.
    Query params: search, crop_name, district, max_price, is_organic, farmer_id, status, page, per_page
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)
    search = request.args.get("search")
    crop_name = request.args.get("crop_name")
    district = request.args.get("district")
    max_price = request.args.get("max_price", type=float)
    is_organic = request.args.get("is_organic")
    farmer_id = request.args.get("farmer_id", type=int)
    status = request.args.get("status", "active")

    query = ProduceListing.query
    if status and status != "all":
        query = query.filter_by(status=status)

    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if crop_name:
        query = query.filter(ProduceListing.crop_name.ilike(f"%{crop_name}%"))
    if district and district != "All":
        query = query.filter(ProduceListing.district.ilike(f"%{district}%"))
    if search:
        s = f"%{search}%"
        query = query.filter(
            db.or_(
                ProduceListing.crop_name.ilike(s),
                ProduceListing.variety.ilike(s),
                ProduceListing.description.ilike(s),
                ProduceListing.location.ilike(s),
                ProduceListing.district.ilike(s),
            )
        )
    if max_price is not None:
        query = query.filter(ProduceListing.asking_price_per_kg <= max_price)
    if is_organic is not None:
        org_bool = str(is_organic).lower() in ["true", "1", "yes"]
        query = query.filter(ProduceListing.is_organic == org_bool)

    pagination = query.order_by(ProduceListing.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response({
        "items": [item.to_dict() for item in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    })


def get_listing_detail(listing_id):
    """Get single produce listing details."""
    listing = ProduceListing.query.get(listing_id)
    if not listing:
        return error_response("Produce listing not found", 404)
    return success_response(listing.to_dict())


def create_listing():
    """
    Farmer creates a produce listing with available kilos and asking price.
    Automatically notifies all other users in the platform about the fresh produce.
    """
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    data = request.get_json(silent=True) or {}
    crop_name = data.get("crop_name")
    asking_price = data.get("asking_price_per_kg")
    quantity_kg = data.get("total_quantity_kg") or data.get("quantity_kg")

    if not crop_name or asking_price is None or quantity_kg is None:
        return error_response("crop_name, total_quantity_kg, and asking_price_per_kg are required", 400)

    try:
        asking_price = float(asking_price)
        quantity_kg = float(quantity_kg)
    except (ValueError, TypeError):
        return error_response("Price and quantity must be valid numbers", 400)

    min_price = data.get("min_acceptable_price_per_kg")
    if min_price is not None:
        try:
            min_price = float(min_price)
        except (ValueError, TypeError):
            min_price = None

    listing = ProduceListing(
        farmer_id=user.id,
        crop_id=data.get("crop_id"),
        crop_name=crop_name.strip(),
        variety=data.get("variety", "Local"),
        total_quantity_kg=quantity_kg,
        available_quantity_kg=quantity_kg,
        asking_price_per_kg=asking_price,
        min_acceptable_price_per_kg=min_price or asking_price * 0.85,
        district=data.get("district") or user.district or "Vavuniya",
        location=data.get("location") or user.farm_location or user.ds_division,
        harvest_date=data.get("harvest_date") or "Freshly Harvested",
        is_organic=bool(data.get("is_organic", True)),
        is_negotiable=bool(data.get("is_negotiable", True)),
        description=data.get("description"),
        image_url=data.get("image_url"),
        status="active",
    )

    db.session.add(listing)
    db.session.flush()

    # BROADCAST NOTIFICATION: Send in-app notification to all other active users except the creator
    other_users = User.query.filter(User.id != user.id, User.status == "active").all()
    for other in other_users:
        notif = MarketNotification(
            user_id=other.id,
            sender_id=user.id,
            title=f"🌾 Fresh {listing.crop_name} Available!",
            message=f"{user.full_name} listed {listing.total_quantity_kg} kg of {listing.crop_name} at Rs. {listing.asking_price_per_kg:.2f}/kg in {listing.district}.",
            category="marketplace",
            link_url=f"/consumer?listing_id={listing.id}",
            is_read=False,
        )
        db.session.add(notif)

    db.session.commit()

    return success_response(listing.to_dict(), message="Produce listing created and broadcast to marketplace!", status_code=201)


def update_listing(listing_id):
    """Update a produce listing."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    listing = ProduceListing.query.get(listing_id)
    if not listing:
        return error_response("Produce listing not found", 404)

    if listing.farmer_id != user.id and user.role not in ["admin", "super_admin"]:
        return error_response("Only the seller or admin can edit this listing", 403)

    data = request.get_json(silent=True) or {}
    fields = (
        "crop_name", "variety", "total_quantity_kg", "available_quantity_kg",
        "asking_price_per_kg", "min_acceptable_price_per_kg", "district",
        "location", "harvest_date", "is_organic", "is_negotiable", "description",
        "image_url", "status"
    )
    for f in fields:
        if f in data:
            val = data[f]
            if f in ["total_quantity_kg", "available_quantity_kg", "asking_price_per_kg", "min_acceptable_price_per_kg"] and val is not None:
                val = float(val)
            setattr(listing, f, val)

    db.session.commit()
    return success_response(listing.to_dict(), message="Produce listing updated successfully")


def delete_listing(listing_id):
    """Delete or close a produce listing."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    listing = ProduceListing.query.get(listing_id)
    if not listing:
        return error_response("Produce listing not found", 404)

    if listing.farmer_id != user.id and user.role not in ["admin", "super_admin"]:
        return error_response("Only the seller or admin can delete this listing", 403)

    db.session.delete(listing)
    db.session.commit()
    return success_response(message="Listing deleted successfully")


def create_bargain_offer(listing_id):
    """
    Buyer/Consumer submits a bargain offer for a quantity of produce at an offered price per kg.
    Notifies the seller farmer.
    """
    buyer = get_current_user()
    if not buyer:
        return error_response("Authentication required", 401)

    listing = ProduceListing.query.get(listing_id)
    if not listing:
        return error_response("Produce listing not found", 404)

    if listing.status != "active" or listing.available_quantity_kg <= 0:
        return error_response("This produce is currently unavailable or sold out", 400)

    if listing.farmer_id == buyer.id:
        return error_response("You cannot place a bargain offer on your own produce listing", 400)

    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity_kg")
    offered_price = data.get("offered_price_per_kg")

    if quantity is None or offered_price is None:
        return error_response("quantity_kg and offered_price_per_kg are required", 400)

    try:
        quantity = float(quantity)
        offered_price = float(offered_price)
    except (ValueError, TypeError):
        return error_response("Quantity and price must be valid numbers", 400)

    if quantity <= 0 or offered_price <= 0:
        return error_response("Quantity and price must be greater than zero", 400)

    if quantity > listing.available_quantity_kg:
        return error_response(f"Only {listing.available_quantity_kg} kg available for this listing", 400)

    total_amount = round(quantity * offered_price, 2)
    buyer_message = data.get("buyer_message", "").strip()

    offer = BargainOffer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        farmer_id=listing.farmer_id,
        quantity_kg=quantity,
        offered_price_per_kg=offered_price,
        total_amount=total_amount,
        buyer_message=buyer_message,
        status="pending",
    )

    db.session.add(offer)

    # Notify the farmer
    notif = MarketNotification(
        user_id=listing.farmer_id,
        sender_id=buyer.id,
        title=f"🤝 Bargain Offer Received for {listing.crop_name}!",
        message=f"{buyer.full_name} offered Rs. {offered_price:.2f}/kg for {quantity} kg (Total: Rs. {total_amount:.2f})." + (f" Note: \"{buyer_message}\"" if buyer_message else ""),
        category="bargain",
        link_url=f"/marketplace?tab=incoming_offers&offer_id={offer.id}",
        is_read=False,
    )
    db.session.add(notif)

    db.session.commit()

    return success_response(offer.to_dict(), message="Bargain offer sent to the farmer!", status_code=201)


def get_my_offers():
    """Get all bargain offers sent by the logged-in buyer."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    offers = BargainOffer.query.filter_by(buyer_id=user.id).order_by(BargainOffer.created_at.desc()).all()
    return success_response([o.to_dict() for o in offers])


def get_incoming_offers():
    """Get all bargain offers received by the logged-in farmer."""
    user = get_current_user()
    if not user:
        return error_response("Authentication required", 401)

    offers = BargainOffer.query.filter_by(farmer_id=user.id).order_by(BargainOffer.created_at.desc()).all()
    return success_response([o.to_dict() for o in offers])


def respond_to_offer(offer_id):
    """
    Farmer responds to an offer: accept, reject, or counter.
    Payload: {"action": "accept"|"reject"|"counter", "counter_price_per_kg": float, "counter_message": str}
    """
    farmer = get_current_user()
    if not farmer:
        return error_response("Authentication required", 401)

    offer = BargainOffer.query.get(offer_id)
    if not offer:
        return error_response("Bargain offer not found", 404)

    if offer.farmer_id != farmer.id and farmer.role not in ["admin", "super_admin"]:
        return error_response("Only the seller farmer can respond to this offer", 403)

    if offer.status not in ["pending", "countered"]:
        return error_response(f"Offer is already {offer.status}", 400)

    data = request.get_json(silent=True) or {}
    action = data.get("action", "").lower().strip()

    listing = offer.listing

    if action == "accept":
        offer.status = "accepted"
        offer.agreed_price_per_kg = offer.offered_price_per_kg
        offer.agreed_total_amount = offer.total_amount

        # Update available quantity
        if listing:
            listing.available_quantity_kg = max(0.0, listing.available_quantity_kg - offer.quantity_kg)
            if listing.available_quantity_kg <= 0:
                listing.status = "sold_out"

        notif = MarketNotification(
            user_id=offer.buyer_id,
            sender_id=farmer.id,
            title=f"🎉 Bargain Accepted for {listing.crop_name if listing else 'Produce'}!",
            message=f"{farmer.full_name} accepted your offer of Rs. {offer.offered_price_per_kg:.2f}/kg for {offer.quantity_kg} kg (Total: Rs. {offer.total_amount:.2f}). Contact the farmer in chat to arrange delivery.",
            category="bargain",
            link_url=f"/consumer?tab=deals&offer_id={offer.id}",
            is_read=False,
        )
        db.session.add(notif)

    elif action == "counter":
        counter_price = data.get("counter_price_per_kg")
        if counter_price is None:
            return error_response("counter_price_per_kg is required for counter-offer", 400)
        try:
            counter_price = float(counter_price)
        except (ValueError, TypeError):
            return error_response("counter_price_per_kg must be a valid number", 400)

        offer.status = "countered"
        offer.counter_price_per_kg = counter_price
        offer.counter_message = data.get("counter_message", "").strip()

        notif = MarketNotification(
            user_id=offer.buyer_id,
            sender_id=farmer.id,
            title=f"💬 Counter-Offer on {listing.crop_name if listing else 'Produce'}",
            message=f"{farmer.full_name} suggested Rs. {counter_price:.2f}/kg for your {offer.quantity_kg} kg request." + (f" Note: \"{offer.counter_message}\"" if offer.counter_message else ""),
            category="bargain",
            link_url=f"/consumer?tab=bargains&offer_id={offer.id}",
            is_read=False,
        )
        db.session.add(notif)

    elif action == "reject":
        offer.status = "rejected"
        reason = data.get("reason", "").strip()

        notif = MarketNotification(
            user_id=offer.buyer_id,
            sender_id=farmer.id,
            title=f"Offer Update for {listing.crop_name if listing else 'Produce'}",
            message=f"{farmer.full_name} declined your offer of Rs. {offer.offered_price_per_kg:.2f}/kg." + (f" Reason: \"{reason}\"" if reason else ""),
            category="bargain",
            link_url=f"/consumer?tab=bargains",
            is_read=False,
        )
        db.session.add(notif)

    else:
        return error_response("Invalid action. Must be accept, counter, or reject", 400)

    db.session.commit()
    return success_response(offer.to_dict(), message=f"Offer response '{action}' saved successfully")


def accept_counter_offer(offer_id):
    """
    Buyer accepts farmer's counter offer.
    """
    buyer = get_current_user()
    if not buyer:
        return error_response("Authentication required", 401)

    offer = BargainOffer.query.get(offer_id)
    if not offer:
        return error_response("Bargain offer not found", 404)

    if offer.buyer_id != buyer.id:
        return error_response("Only the buyer can accept this counter offer", 403)

    if offer.status != "countered" or not offer.counter_price_per_kg:
        return error_response("Offer is not in countered status", 400)

    listing = offer.listing
    offer.status = "accepted"
    offer.agreed_price_per_kg = offer.counter_price_per_kg
    offer.agreed_total_amount = round(offer.quantity_kg * offer.counter_price_per_kg, 2)

    if listing:
        listing.available_quantity_kg = max(0.0, listing.available_quantity_kg - offer.quantity_kg)
        if listing.available_quantity_kg <= 0:
            listing.status = "sold_out"

    notif = MarketNotification(
        user_id=offer.farmer_id,
        sender_id=buyer.id,
        title=f"🎉 Counter-Offer Accepted for {listing.crop_name if listing else 'Produce'}!",
        message=f"{buyer.full_name} accepted your counter price of Rs. {offer.agreed_price_per_kg:.2f}/kg for {offer.quantity_kg} kg (Total: Rs. {offer.agreed_total_amount:.2f}).",
        category="bargain",
        link_url=f"/marketplace?tab=incoming_offers&offer_id={offer.id}",
        is_read=False,
    )
    db.session.add(notif)

    db.session.commit()
    return success_response(offer.to_dict(), message="Counter offer accepted! Deal confirmed.")
