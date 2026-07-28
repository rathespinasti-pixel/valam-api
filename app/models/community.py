from datetime import datetime
from app.extensions import db


class CommunityPost(db.Model):
    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General", index=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("Comment", backref="post", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_comments=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "author_name": self.author.full_name if self.author else "Farmer",
            "author_location": self.author.farm_location if self.author else "Vavuniya",
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "image_url": self.image_url,
            "comment_count": len(self.comments),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_comments:
            data["comments"] = [c.to_dict() for c in sorted(self.comments, key=lambda x: x.created_at)]
        return data


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("community_posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "author_name": self.author.full_name if self.author else "Farmer",
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
