from datetime import datetime
from app.extensions import db

class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    level = db.Column(db.String(20), nullable=False, default="FREE")  # FREE, PLUS, PRO
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # optional expiry

    user = db.relationship("User", backref=db.backref("subscription", uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "level": self.level,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    def has_marketplace_access(self):
        """Return True if subscription level is PRO, granting marketplace access."""
        return self.level.upper() == "PRO"
