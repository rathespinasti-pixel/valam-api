from datetime import datetime
from app.extensions import db


class DiseaseDiagnosis(db.Model):
    __tablename__ = "disease_diagnoses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crop_name = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis_result = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text, nullable=False)
    disclaimer = db.Column(
        db.String(255),
        default="This AI analysis provides guidance only and does not replace professional agricultural extension officer diagnosis.",
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop_name": self.crop_name,
            "image_url": self.image_url,
            "symptoms": self.symptoms,
            "diagnosis_result": self.diagnosis_result,
            "recommendations": self.recommendations,
            "disclaimer": self.disclaimer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
