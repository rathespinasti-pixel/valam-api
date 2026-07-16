from datetime import datetime

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), default="kg")  # kg, ton, piece, etc.
    quantity_available = db.Column(db.Float, default=0)
    image_url = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": float(self.price) if self.price is not None else None,
            "unit": self.unit,
            "quantity_available": self.quantity_available,
            "image_url": self.image_url,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
