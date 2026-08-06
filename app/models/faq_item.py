from datetime import datetime
from app.extensions import db


class FAQItem(db.Model):
    __tablename__ = "faq_items"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General", nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    order_num = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "is_published": self.is_published,
            "order_num": self.order_num,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
