from datetime import datetime
from app.extensions import db


class AdminActivityLog(db.Model):
    __tablename__ = "admin_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    performed_by = db.Column(db.String(120), nullable=False)
    performed_by_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "performed_by": self.performed_by,
            "performed_by_id": self.performed_by_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
            "time": self.created_at.strftime("%H:%M:%S") if self.created_at else None,
        }
