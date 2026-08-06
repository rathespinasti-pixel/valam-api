from datetime import datetime
from app.extensions import db


class UserFeedback(db.Model):
    __tablename__ = "user_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False) # pending, replied, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "admin_reply": self.admin_reply,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
