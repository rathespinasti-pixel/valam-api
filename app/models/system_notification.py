from datetime import datetime
from app.extensions import db


class SystemNotification(db.Model):
    __tablename__ = "system_notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="Alert", nullable=False) # Alert, Fertilizer, Weather, Disease
    target_type = db.Column(db.String(50), default="All Users", nullable=False) # All Users, District, Crop, Category
    target_value = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="sent", nullable=False) # draft, scheduled, sent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "target_type": self.target_type,
            "target_value": self.target_value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
