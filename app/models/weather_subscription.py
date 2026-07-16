from datetime import datetime

from app.extensions import db


class WeatherSubscription(db.Model):
    __tablename__ = "weather_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    alert_types = db.Column(db.String(255), default="all")  # e.g. "rain,storm,frost"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "alert_types": self.alert_types,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
