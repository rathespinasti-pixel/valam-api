from datetime import datetime
from app.extensions import db


class DiseaseCatalog(db.Model):
    __tablename__ = "disease_catalog"

    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(120), nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    causes = db.Column(db.Text, nullable=True)
    organic_treatment = db.Column(db.Text, nullable=True)
    chemical_treatment = db.Column(db.Text, nullable=True)
    prevention_tips = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "disease_name": self.disease_name,
            "crop_name": self.crop_name,
            "symptoms": self.symptoms,
            "causes": self.causes,
            "organic_treatment": self.organic_treatment,
            "chemical_treatment": self.chemical_treatment,
            "prevention_tips": self.prevention_tips,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
