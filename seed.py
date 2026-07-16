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

    if not SolarGuide.query.first():
        guides = [
            SolarGuide(
                title="Getting Started with Solar-Powered Irrigation",
                summary="Learn the basics of setting up a solar water pump for your farm.",
                content="Solar-powered irrigation uses photovoltaic panels to run water pumps, "
                        "cutting fuel costs and enabling remote field irrigation. Start by "
                        "assessing your daily water needs, then size your panel array and "
                        "pump accordingly. Consult a certified installer for wiring safety.",
                category="Irrigation",
            ),
            SolarGuide(
                title="Agrivoltaics: Growing Crops Under Solar Panels",
                summary="How to combine crop production with solar energy generation.",
                content="Agrivoltaics involves installing solar panels above farmland while "
                        "crops continue to grow underneath. Shade-tolerant crops like leafy "
                        "greens and berries often thrive, while the farm gains an additional "
                        "energy revenue stream.",
                category="Agrivoltaics",
            ),
            SolarGuide(
                title="Maintaining Your Solar Panels for Maximum Yield",
                summary="Simple maintenance routines to keep your solar setup efficient.",
                content="Regularly clean panels of dust and debris, check wiring connections "
                        "for wear, and monitor output using an inverter app. Scheduling a "
                        "professional inspection once a year helps catch issues early.",
                category="Maintenance",
            ),
        ]
        db.session.bulk_save_objects(guides)

    if not User.query.filter_by(email="demo@farm.com").first():
        demo_user = User(full_name="Demo Farmer", email="demo@farm.com", farm_location="Kurunegala, LK")
        demo_user.set_password("password123")
        db.session.add(demo_user)
        db.session.flush()

        products = [
            Product(owner_id=demo_user.id, name="Fresh Tomatoes", category="Vegetables",
                     price=2.50, unit="kg", quantity_available=100, location="Kurunegala"),
            Product(owner_id=demo_user.id, name="Solar Water Pump", category="Solar Equipment",
                     price=350.00, unit="piece", quantity_available=5, location="Kurunegala"),
        ]
        db.session.bulk_save_objects(products)

    db.session.commit()
    print("Seed data created successfully.")
