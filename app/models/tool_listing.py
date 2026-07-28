from datetime import datetime
from app.extensions import db


class ToolListing(db.Model):
    __tablename__ = "tool_listings"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tool_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default="Equipment")
    rental_price_per_day = db.Column(db.Numeric(10, 2), nullable=False)
    location = db.Column(db.String(100), default="Vavuniya")
    contact_phone = db.Column(db.String(30), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_name": self.owner.full_name if self.owner else "Farmer",
            "tool_name": self.tool_name,
            "description": self.description,
            "category": self.category,
            "rental_price_per_day": float(self.rental_price_per_day) if self.rental_price_per_day is not None else None,
            "location": self.location,
            "contact_phone": self.contact_phone,
            "is_available": self.is_available,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
