from datetime import datetime
from app.extensions import db

class CropLifecycleImage(db.Model):
    __tablename__ = "crop_lifecycle_images"

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=True)
    crop_name = db.Column(db.String(100), nullable=False, index=True)
    stage = db.Column(db.String(50), nullable=False, index=True)
    image_url = db.Column(db.Text, nullable=False)
    prompt_used = db.Column(db.Text, nullable=True)
    # New optional fields for richer image generation
    variety = db.Column(db.String(100), nullable=True)
    planting_method = db.Column(db.String(100), nullable=True)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "crop_id": self.crop_id,
            "crop_name": self.crop_name,
            "stage": self.stage,
            "image_url": self.image_url,
            "prompt_used": self.prompt_used,
            "variety": self.variety,
            "planting_method": self.planting_method,
            "generated_date": self.generated_date.isoformat() if self.generated_date else None,
        }
