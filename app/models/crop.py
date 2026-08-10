from datetime import datetime
from app.extensions import db


class Crop(db.Model):
    __tablename__ = "crops"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100), nullable=True)
    planting_date = db.Column(db.Date, nullable=False)
    planting_method = db.Column(db.String(50), nullable=True, default="Transplanting")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    land_size = db.Column(db.Float, nullable=True, default=0.5)
    land_size_unit = db.Column(db.String(20), nullable=True, default="Acres")
    irrigation_type = db.Column(db.String(50), nullable=True, default="Drip Irrigation")
    fertilizer_preference = db.Column(db.String(50), nullable=True, default="Organic")
    area_size = db.Column(db.String(50), nullable=True)
    current_stage = db.Column(db.String(50), nullable=False, default="Stage 1: Seedling / Nursery")
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "variety": self.variety,
            "planting_date": self.planting_date.isoformat() if self.planting_date else None,
            "planting_method": self.planting_method or "Transplanting",
            "land_size": self.land_size if self.land_size is not None else 0.5,
            "land_size_unit": self.land_size_unit or "Acres",
            "irrigation_type": self.irrigation_type or "Drip Irrigation",
            "fertilizer_preference": self.fertilizer_preference or "Organic",
            "area_size": self.area_size or f"{self.land_size or 0.5} {self.land_size_unit or 'Acres'}",
            "current_stage": self.current_stage,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
