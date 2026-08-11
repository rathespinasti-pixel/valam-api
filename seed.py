"""
Simple seed script for demo/testing data.
Run with: python seed.py
"""
from app import create_app
from app.extensions import db
from app.models.solar_guide import SolarGuide
from app.models.user import User
from app.models.product import Product

app = create_app("development")

with app.app_context():
    db.create_all()



    # Ensure Admin user exists
    admin_user = User.query.filter_by(email="admin@gmail.com").first()
    if not admin_user:
        admin_user = User(
            full_name="System Administrator",
            email="admin@gmail.com",
            phone="0771234567",
            farm_location="Vavuniya, LK",
            role="admin",
            status="active",
            farming_category="Admin",
            district="Vavuniya",
            ds_division="Vavuniya Town",
            preferred_language="en",
            onboarding_completed=True,
        )
        admin_user.set_password("Admin@1234")
        db.session.add(admin_user)
    else:
        admin_user.role = "admin"
        admin_user.status = "active"
        admin_user.set_password("Admin@1234")

    # Ensure Demo farmer exists
    demo_user = User.query.filter_by(email="demo@farm.com").first()
    if not demo_user:
        demo_user = User(
            full_name="Demo Farmer",
            email="demo@farm.com",
            phone="0779876543",
            farm_location="Kurunegala, LK",
            role="farmer",
            status="active",
            farming_category="Farmer",
            district="Kurunegala",
            preferred_language="en",
            onboarding_completed=True,
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)

    db.session.commit()
    print("Seed data created successfully.")
