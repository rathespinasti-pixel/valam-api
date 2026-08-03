import os
from datetime import date
from app import create_app
from app.extensions import db
from app.models.crop_guide import CropGuide
from app.models.community import CommunityPost, Comment
from app.models.tool_listing import ToolListing
from app.models.user import User

app = create_app(os.getenv("FLASK_CONFIG", "development"))

from sqlalchemy import text, inspect

def seed_database():
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                pass
        except Exception:
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///valam_local.db"
            db.engine.dispose()

        db.create_all()

        # Ensure new columns exist on users and crops tables if database already existed
        try:
            inspector = inspect(db.engine)
            existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
            new_user_cols = [
                ("farming_category", "VARCHAR(50) DEFAULT 'Farmer'"),
                ("district", "VARCHAR(100) DEFAULT 'Vavuniya'"),
                ("ds_division", "VARCHAR(100) DEFAULT 'Vavuniya Town'"),
                ("gn_division", "VARCHAR(100)"),
                ("land_size", "FLOAT DEFAULT 1.0"),
                ("land_size_unit", "VARCHAR(20) DEFAULT 'Acres'"),
                ("irrigation_preference", "VARCHAR(50) DEFAULT 'Drip Irrigation'"),
                ("fertilizer_preference", "VARCHAR(50) DEFAULT 'Organic'"),
                ("district_asc", "VARCHAR(100) DEFAULT 'Vavuniya Town'"),
                ("farmer_type", "VARCHAR(50) DEFAULT 'Farmer'"),
                ("farming_experience", "VARCHAR(50)"),
                ("main_crops_grown", "VARCHAR(255)"),
                ("preferred_language", "VARCHAR(10) DEFAULT 'en'"),
                ("onboarding_completed", "BOOLEAN DEFAULT FALSE"),
            ]
            for col_name, col_def in new_user_cols:
                if col_name not in existing_user_cols:
                    db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                    db.session.commit()

            if "crops" in inspector.get_table_names():
                existing_crop_cols = [c['name'] for c in inspector.get_columns('crops')]
                new_crop_cols = [
                    ("planting_method", "VARCHAR(50) DEFAULT 'Transplanting'"),
                    ("land_size", "FLOAT DEFAULT 0.5"),
                    ("land_size_unit", "VARCHAR(20) DEFAULT 'Acres'"),
                    ("irrigation_type", "VARCHAR(50) DEFAULT 'Drip Irrigation'"),
                    ("fertilizer_preference", "VARCHAR(50) DEFAULT 'Organic'"),
                ]
                for col_name, col_def in new_crop_cols:
                    if col_name not in existing_crop_cols:
                        db.session.execute(text(f"ALTER TABLE crops ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()

            if "disease_diagnoses" in inspector.get_table_names():
                existing_diag_cols = [c['name'] for c in inspector.get_columns('disease_diagnoses')]
                new_diag_cols = [
                    ("cause", "TEXT"),
                    ("organic_treatment", "TEXT"),
                    ("chemical_treatment", "TEXT"),
                    ("prevention_advice", "TEXT"),
                    ("language", "VARCHAR(10) DEFAULT 'en'"),
                ]
                for col_name, col_def in new_diag_cols:
                    if col_name not in existing_diag_cols:
                        db.session.execute(text(f"ALTER TABLE disease_diagnoses ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Note on column migration: {e}")

        # Check or create default admin/farmer user
        user = User.query.filter_by(email="demo@valam.lk").first()
        if not user:
            user = User(
                full_name="Ketheeswaran Vavuniya",
                email="demo@valam.lk",
                phone="0771234567",
                farm_location="Vavuniya South",
                farm_size_acres=2.5,
                role="farmer",
                district_asc="Vavuniya ASC Division",
                farmer_type="Small-scale farmer",
                farming_experience="3-5 years",
                main_crops_grown="Tomato, Chili, Onion",
                preferred_language="ta",
                onboarding_completed=True,
            )
            user.set_password("valam123")
            db.session.add(user)
            db.session.commit()
            print("Created demo user: demo@valam.lk / valam123")

        # 1. Seed Crop Guides
        if CropGuide.query.count() == 0:
            guides_data = [
                {
                    "crop_name": "Tomato",
                    "variety": "Thilina / KC1",
                    "recommended_season": "Yala & Maha",
                    "water_requirements": "Requires 4-6 liters per plant weekly. Critical watering during flowering and fruit setting stages. Avoid overhead watering to prevent blight.",
                    "fertilizer_guidance": "Week 1: Basal fertilizer (NPK 15:15:15). Week 3 & 6: Top dressing with Urea and MOP.",
                    "common_problems": "Bacterial Wilt, Early Blight, Tomato Fruit Borer, Leaf Curl Virus",
                    "basic_solutions": "Use disease-resistant varieties, apply neem oil extract for whiteflies, maintain crop rotation with legumes.",
                    "image_url": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=600&q=80",
                    "stages": [
                        {"week": "Week 1", "stage": "Nursery & Seed Prep", "advice": "Sow seeds in seedling trays or prepared nursery beds. Protect from heavy rain."},
                        {"week": "Week 3", "stage": "Transplanting", "advice": "Transplant 21-day healthy seedlings at 60cm x 45cm spacing in raised beds."},
                        {"week": "Week 6", "stage": "Vegetative & Staking", "advice": "Erect bamboo stakes to support indeterminate vines. Apply first top dressing."},
                        {"week": "Week 9", "stage": "Flowering & Fruit Set", "advice": "Maintain consistent drip irrigation. Inspect for fruit borer caterpillars."},
                        {"week": "Week 12", "stage": "Harvesting", "advice": "Pick ripe fruits at breaker stage in early morning hours."}
                    ]
                },
                {
                    "crop_name": "Chili",
                    "variety": "MICO-1 / Waraniya",
                    "recommended_season": "Yala",
                    "water_requirements": "Moderate water requirement. Drip irrigation every 2 days. Avoid soil waterlogging.",
                    "fertilizer_guidance": "Basal application of compost (10 t/ha). Top dressing with nitrogen every 3 weeks after transplanting.",
                    "common_problems": "Chili Leaf Curl Virus, Thrips, Anthracnose (Fruit rot), Powdery Mildew",
                    "basic_solutions": "Yellow sticky traps for thrips, spray sulfur for mildew, remove virus-infected plants immediately.",
                    "image_url": "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80",
                    "stages": [
                        {"week": "Week 1-4", "stage": "Nursery Management", "advice": "Raise seedlings under 50% shade net to shield from thrips vectors."},
                        {"week": "Week 5", "stage": "Field Planting", "advice": "Transplant seedlings on ridges. Apply straw mulch to conserve moisture."},
                        {"week": "Week 8", "stage": "Branching & Flowering", "advice": "Pinch off first flower bud to encourage bushy branching. Apply potassium spray."},
                        {"week": "Week 12-16", "stage": "Pickings & Harvest", "advice": "Harvest green chilies every 5-7 days."}
                    ]
                },
                {
                    "crop_name": "Red Onion",
                    "variety": "Vavuniya Local / Jaffna Local",
                    "recommended_season": "Yala (May - August)",
                    "water_requirements": "Light & frequent watering every 2 days. Stop irrigation 10 days before harvest.",
                    "fertilizer_guidance": "High potassium requirement. Apply recommended Department of Agriculture basal mixture.",
                    "common_problems": "Purple Blotch, Onion Thrips, Root Rot",
                    "basic_solutions": "Ensure well-drained sandy loam soil, avoid excess nitrogen, use bio-fungicide Trichoderma.",
                    "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80",
                    "stages": [
                        {"week": "Week 1", "stage": "Bulbing Preparation", "advice": "Plant healthy seed bulbs at 10cm spacing in flat beds."},
                        {"week": "Week 3", "stage": "Foliar Growth", "advice": "Weeding and light earthing up. Apply initial top dressing."},
                        {"week": "Week 7", "stage": "Bulb Swelling", "advice": "Ensure moisture consistency. Monitor leaves for purple blotch spots."},
                        {"week": "Week 10", "stage": "Maturation & Curing", "advice": "Top neck fall indicates maturity. Harvest and sun-cure bulbs."}
                    ]
                },
                {
                    "crop_name": "Paddy",
                    "variety": "Bg 352 / At 362",
                    "recommended_season": "Maha (October - March)",
                    "water_requirements": "Continuous standing water (2-5cm) during tillering; drain field 2 weeks before harvest.",
                    "fertilizer_guidance": "Apply Department of Agriculture recommended fertilizer pack (Urea, TSP, MOP).",
                    "common_problems": "Paddy Stem Borer, Brown Planthopper (BPH), Blast Disease",
                    "basic_solutions": "Maintain light traps for moths, avoid excessive nitrogen fertilization, conserve natural predator spiders.",
                    "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80",
                    "stages": [
                        {"week": "Week 1", "stage": "Land Prep & Sowing", "advice": "Puddle land thoroughly. Broadcast sprouted seed paddy evenly."},
                        {"week": "Week 4", "stage": "Tillering Stage", "advice": "Apply 1st top dressing urea. Maintain 3cm standing water level."},
                        {"week": "Week 8", "stage": "Panicle Initiation", "advice": "Apply 2nd top dressing MOP. Inspect for stem borer dead hearts."},
                        {"week": "Week 14", "stage": "Grain Filling & Harvest", "advice": "Drain field when 80% panicles turn golden yellow."}
                    ]
                }
            ]

            for g_data in guides_data:
                stages = g_data.pop("stages")
                guide = CropGuide(**g_data)
                guide.set_growth_stages(stages)
                db.session.add(guide)
            
            db.session.commit()
            print(f"Seeded {len(guides_data)} crop guides.")

        # 2. Seed Community Posts
        if CommunityPost.query.count() == 0:
            posts = [
                CommunityPost(
                    user_id=user.id,
                    title="Best organic remedy for chili thrips in Vavuniya?",
                    content="My Yala chili plants are showing leaf curling at the tips. Has anyone tried neem oil + garlic spray solution with success in our area?",
                    category="Pest Control",
                    image_url="https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80",
                ),
                CommunityPost(
                    user_id=user.id,
                    title="Solar water pump experience after 6 months",
                    content="Installed a 3HP solar irrigation pump in Omanthai. Cut diesel costs completely! Happy to share supplier details and subsidy application tips.",
                    category="Equipment & Solar",
                ),
            ]
            db.session.add_all(posts)
            db.session.commit()

            c1 = Comment(post_id=posts[0].id, user_id=user.id, content="Neem oil 5ml per liter with soapy water works well if sprayed early morning!")
            db.session.add(c1)
            db.session.commit()
            print("Seeded sample community posts.")

        # 3. Seed Tool Listings
        if ToolListing.query.count() == 0:
            tools = [
                ToolListing(
                    owner_id=user.id,
                    tool_name="Water Pump 2-inch Diesel",
                    description="Heavy duty 2-inch diesel water pump for field irrigation. Includes 50m delivery hose.",
                    category="Irrigation Pump",
                    rental_price_per_day=1500.00,
                    location="Vavuniya Town",
                    contact_phone="0771234567",
                    image_url="https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80",
                ),
                ToolListing(
                    owner_id=user.id,
                    tool_name="Knapsack Battery Sprayer (16L)",
                    description="Rechargeable battery power sprayer for liquid fertilizer & pesticide application.",
                    category="Sprayer",
                    rental_price_per_day=500.00,
                    location="Pambaimadu",
                    contact_phone="0771234567",
                ),
            ]
            db.session.add_all(tools)
            db.session.commit()
            print("Seeded sample tool listings.")

        print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
