from datetime import datetime
from app.extensions import db


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
