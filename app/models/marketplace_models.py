from datetime import datetime
from app.extensions import db


class ProduceListing(db.Model):
    __tablename__ = "produce_listings"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=True)
    crop_name = db.Column(db.String(100), nullable=False, index=True)
    variety = db.Column(db.String(100), nullable=True)
    total_quantity_kg = db.Column(db.Float, nullable=False, default=10.0)
    available_quantity_kg = db.Column(db.Float, nullable=False, default=10.0)
    asking_price_per_kg = db.Column(db.Float, nullable=False)
    min_acceptable_price_per_kg = db.Column(db.Float, nullable=True)
    district = db.Column(db.String(100), nullable=False, default="Vavuniya", index=True)
    location = db.Column(db.String(255), nullable=True)
    harvest_date = db.Column(db.String(50), nullable=True)
    is_organic = db.Column(db.Boolean, default=True)
    is_negotiable = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(30), default="active", nullable=False, index=True)  # active, sold_out, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farmer = db.relationship("User", foreign_keys=[farmer_id], backref=db.backref("produce_listings", lazy=True, cascade="all, delete-orphan"))
    offers = db.relationship("BargainOffer", backref="listing", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_farmer=True):
        data = {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "crop_id": self.crop_id,
            "crop_name": self.crop_name,
            "variety": self.variety or "Local",
            "total_quantity_kg": self.total_quantity_kg,
            "available_quantity_kg": self.available_quantity_kg,
            "asking_price_per_kg": self.asking_price_per_kg,
            "min_acceptable_price_per_kg": self.min_acceptable_price_per_kg,
            "district": self.district,
            "location": self.location,
            "harvest_date": self.harvest_date,
            "is_organic": self.is_organic,
            "is_negotiable": self.is_negotiable,
            "description": self.description,
            "image_url": self.image_url,
            "status": self.status,
            "offers_count": len(self.offers) if self.offers else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_farmer and self.farmer:
            data["farmer"] = {
                "id": self.farmer.id,
                "full_name": self.farmer.full_name,
                "phone": self.farmer.phone,
                "district": self.farmer.district,
                "farming_category": self.farmer.farming_category or "Farmer",
            }
        return data


class BargainOffer(db.Model):
    __tablename__ = "bargain_offers"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("produce_listings.id"), nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    quantity_kg = db.Column(db.Float, nullable=False)
    offered_price_per_kg = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    buyer_message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="pending", nullable=False, index=True)  # pending, accepted, rejected, countered, completed, cancelled
    counter_price_per_kg = db.Column(db.Float, nullable=True)
    counter_message = db.Column(db.Text, nullable=True)
    agreed_price_per_kg = db.Column(db.Float, nullable=True)
    agreed_total_amount = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    buyer = db.relationship("User", foreign_keys=[buyer_id], backref=db.backref("sent_offers", lazy=True))
    farmer = db.relationship("User", foreign_keys=[farmer_id], backref=db.backref("received_offers", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "buyer_id": self.buyer_id,
            "farmer_id": self.farmer_id,
            "quantity_kg": self.quantity_kg,
            "offered_price_per_kg": self.offered_price_per_kg,
            "total_amount": self.total_amount,
            "buyer_message": self.buyer_message,
            "status": self.status,
            "counter_price_per_kg": self.counter_price_per_kg,
            "counter_message": self.counter_message,
            "agreed_price_per_kg": self.agreed_price_per_kg,
            "agreed_total_amount": self.agreed_total_amount,
            "listing": self.listing.to_dict(include_farmer=False) if self.listing else None,
            "buyer": {
                "id": self.buyer.id,
                "full_name": self.buyer.full_name,
                "phone": self.buyer.phone,
                "district": self.buyer.district,
                "role": self.buyer.role,
            } if self.buyer else None,
            "farmer": {
                "id": self.farmer.id,
                "full_name": self.farmer.full_name,
                "phone": self.farmer.phone,
                "district": self.farmer.district,
            } if self.farmer else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DirectMessage(db.Model):
    __tablename__ = "direct_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("produce_listings.id"), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_messages", lazy=True))
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref=db.backref("received_messages", lazy=True))
    listing = db.relationship("ProduceListing", foreign_keys=[listing_id], backref=db.backref("messages", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "listing_id": self.listing_id,
            "message": self.message,
            "is_read": self.is_read,
            "sender": {
                "id": self.sender.id,
                "full_name": self.sender.full_name,
                "role": self.sender.role,
            } if self.sender else None,
            "receiver": {
                "id": self.receiver.id,
                "full_name": self.receiver.full_name,
                "role": self.receiver.role,
            } if self.receiver else None,
            "listing_name": self.listing.crop_name if self.listing else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MarketNotification(db.Model):
    __tablename__ = "market_notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="marketplace", nullable=False)  # marketplace, bargain, chat, alert
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    recipient = db.relationship("User", foreign_keys=[user_id], backref=db.backref("market_notifications", lazy=True, cascade="all, delete-orphan"))
    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_notifications", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sender_id": self.sender_id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "link_url": self.link_url,
            "is_read": self.is_read,
            "sender_name": self.sender.full_name if self.sender else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
