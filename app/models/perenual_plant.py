import json
from datetime import datetime
from app.extensions import db


class PerenualPlant(db.Model):
    __tablename__ = "perenual_plants"

    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False, index=True)
    perenual_id = db.Column(db.Integer, nullable=True)
    scientific_name = db.Column(db.String(255), nullable=True)
    family = db.Column(db.String(100), nullable=True)
    plant_type = db.Column(db.String(100), nullable=True)
    growth_habit = db.Column(db.String(100), nullable=True)
    sunlight_requirement = db.Column(db.String(255), nullable=True)
    water_requirement = db.Column(db.String(255), nullable=True)
    maintenance_level = db.Column(db.String(100), nullable=True)
    soil_preference = db.Column(db.String(255), nullable=True)
    hardiness = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    reference_images_json = db.Column(db.Text, nullable=True)
    raw_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_reference_images(self):
        if not self.reference_images_json:
            return []
        try:
            return json.loads(self.reference_images_json)
        except Exception:
            return []

    def set_reference_images(self, images_list):
        self.reference_images_json = json.dumps(images_list)

    def to_dict(self):
        return {
            "id": self.id,
            "crop_name": self.crop_name,
            "perenual_id": self.perenual_id,
            "scientific_name": self.scientific_name,
            "family": self.family,
            "plant_type": self.plant_type,
            "growth_habit": self.growth_habit,
            "sunlight_requirement": self.sunlight_requirement,
            "water_requirement": self.water_requirement,
            "maintenance_level": self.maintenance_level,
            "soil_preference": self.soil_preference,
            "hardiness": self.hardiness,
            "description": self.description,
            "image_url": self.image_url,
            "reference_images": self.get_reference_images(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
