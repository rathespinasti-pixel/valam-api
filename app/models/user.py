from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    farm_location = db.Column(db.String(255), nullable=True)
    farm_size_acres = db.Column(db.Float, nullable=True)
    role = db.Column(db.String(20), default="farmer", nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)
    ban_reason = db.Column(db.Text, nullable=True)
    farming_category = db.Column(db.String(50), nullable=True, default="Farmer")
    district = db.Column(db.String(100), nullable=True, default="Vavuniya")
    ds_division = db.Column(db.String(100), nullable=True, default="Vavuniya Town")
    gn_division = db.Column(db.String(100), nullable=True)
    land_size = db.Column(db.Float, nullable=True, default=1.0)
    land_size_unit = db.Column(db.String(20), nullable=True, default="Acres")
    irrigation_preference = db.Column(db.String(50), nullable=True, default="Drip Irrigation")
    fertilizer_preference = db.Column(db.String(50), nullable=True, default="Organic")
    district_asc = db.Column(db.String(100), nullable=True, default="Vavuniya Town")
    farmer_type = db.Column(db.String(50), nullable=True, default="Farmer")
    farming_experience = db.Column(db.String(50), nullable=True)
    main_crops_grown = db.Column(db.String(255), nullable=True)
    preferred_language = db.Column(db.String(10), nullable=True, default="en")
    delivery_address = db.Column(db.String(255), nullable=True)
    onboarding_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chat_history = db.relationship("ChatHistory", backref="user", lazy=True, cascade="all, delete-orphan")
    weather_subscriptions = db.relationship("WeatherSubscription", backref="user", lazy=True, cascade="all, delete-orphan")
    products = db.relationship("Product", backref="owner", lazy=True, cascade="all, delete-orphan")
    crops = db.relationship("Crop", backref="user", lazy=True, cascade="all, delete-orphan")
    diagnoses = db.relationship("DiseaseDiagnosis", backref="user", lazy=True, cascade="all, delete-orphan")
    posts = db.relationship("CommunityPost", backref="author", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy=True, cascade="all, delete-orphan")
    tools = db.relationship("ToolListing", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "farm_location": self.farm_location,
            "farm_size_acres": self.farm_size_acres,
            "role": self.role,
            "status": self.status or "active",
            "ban_reason": self.ban_reason,
            "farming_category": self.farming_category or self.farmer_type or "Farmer",
            "district": self.district or "Vavuniya",
            "ds_division": self.ds_division or self.district_asc or "Vavuniya Town",
            "gn_division": self.gn_division,
            "land_size": self.land_size if self.land_size is not None else self.farm_size_acres,
            "land_size_unit": self.land_size_unit or "Acres",
            "irrigation_preference": self.irrigation_preference or "Drip Irrigation",
            "fertilizer_preference": self.fertilizer_preference or "Organic",
            "district_asc": self.district_asc,
            "farmer_type": self.farmer_type,
            "farming_experience": self.farming_experience,
            "main_crops_grown": self.main_crops_grown,
            "preferred_language": self.preferred_language or "en",
            "delivery_address": self.delivery_address,
            "onboarding_completed": self.onboarding_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
