import json
from datetime import datetime
from app.extensions import db


class CropGuide(db.Model):
    __tablename__ = "crop_guides"

    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False, index=True)
    variety = db.Column(db.String(100), nullable=True)
    recommended_season = db.Column(db.String(100), nullable=True)  # Yala, Maha, All season
    growth_stages_json = db.Column(db.Text, nullable=True)  # JSON formatted stage advice
    water_requirements = db.Column(db.Text, nullable=True)
    fertilizer_guidance = db.Column(db.Text, nullable=True)
    common_problems = db.Column(db.Text, nullable=True)
    basic_solutions = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_growth_stages(self):
        if not self.growth_stages_json:
            return []
        try:
            return json.loads(self.growth_stages_json)
        except Exception:
            return []

    def set_growth_stages(self, stages):
        self.growth_stages_json = json.dumps(stages)

    def to_dict(self):
        return {
            "id": self.id,
            "crop_name": self.crop_name,
            "variety": self.variety,
            "recommended_season": self.recommended_season,
            "growth_stages": self.get_growth_stages(),
            "water_requirements": self.water_requirements,
            "fertilizer_guidance": self.fertilizer_guidance,
            "common_problems": self.common_problems,
            "basic_solutions": self.basic_solutions,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
