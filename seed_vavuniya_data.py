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
            if "users" in inspector.get_table_names():
                existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
                if "status" not in existing_user_cols:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Note on column migration: {e}")

        # Seed Default Super Admin Account
        admin_user = User.query.filter_by(email="admin@gmail.com").first()
        if not admin_user:
            admin_user = User(
                full_name="Super Admin",
                email="admin@gmail.com",
                phone="+94 77 000 0000",
                farm_location="Vavuniya, LK",
                farm_size_acres=5.0,
                role="super_admin",
                status="active",
                district="Vavuniya",
                ds_division="Vavuniya Town",
                onboarding_completed=True,
            )
            admin_user.set_password("Admin@1234")
            db.session.add(admin_user)
            db.session.commit()
            print("Seeded Super Admin account: admin@gmail.com / Admin@1234")
        else:
            admin_user.role = "super_admin"
            admin_user.status = "active"
            db.session.commit()
            print("Super Admin account verified: admin@gmail.com")

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
        guides_data = [
            {
                "crop_name": "Tomato",
                "variety": "Thilina / KC1",
                "recommended_season": "Yala & Maha",
                "water_requirements": "Requires 3.5 - 4.5 liters per plant weekly. Critical watering during flowering and fruit setting stages. Avoid overhead watering to prevent early blight.",
                "fertilizer_guidance": "Week 1: Basal compost (10 t/ha). Week 3 & 6: Top dressing with Urea and MOP.",
                "common_problems": "Bacterial Wilt, Early Blight, Tomato Fruit Borer, Whiteflies",
                "basic_solutions": "Use disease-resistant varieties, apply neem oil extract for whiteflies, maintain crop rotation.",
                "image_url": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=600&q=80",
                "stages": [
                    {
                        "stage_id": 1,
                        "stage_name": "Seedling / Nursery",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 20,
                        "description": "Sow seeds in seedling trays or prepared nursery beds. Protect fragile tender sprouts from heavy rainfall.",
                        "expected_appearance": "Tender green seedlings emerging with 2 to 4 true leaves.",
                        "daily_tasks": ["Water early morning with fine mist sprayer", "Inspect nursery for dampening-off fungus", "Provide 50% shade net shielding"],
                        "water_requirement": "1.0 L/m² daily (Moist soil without waterlogging)",
                        "fertilizer_recommendation": "Basal compost layer & weekly dilute vermicompost tea spray",
                        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Vegetative Growth",
                        "icon": "🌿",
                        "start_day": 21,
                        "end_day": 45,
                        "description": "Transplant 21-day seedlings to raised beds. Erect bamboo stakes to support indeterminate vines.",
                        "expected_appearance": "Sturdy main vine with vigorous dark green foliage and strong lateral branching.",
                        "daily_tasks": ["Staking vines with twines", "Prune lower side suckers", "Apply organic straw mulch around stem"],
                        "water_requirement": "2.5 L/m² daily via drip irrigation",
                        "fertilizer_recommendation": "Top dressing with Urea (15g/m²) or high-Nitrogen compost mixture",
                        "image_url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Flowering",
                        "icon": "🌸",
                        "start_day": 46,
                        "end_day": 70,
                        "description": "Cluster of bright yellow flowers blooming. Steady moisture is crucial to prevent flower drop.",
                        "expected_appearance": "Vibrant yellow star-shaped flower clusters opening on main and lateral branches.",
                        "daily_tasks": ["Inspect leaf underside for whiteflies", "Gently tap trellis wires for pollination boost", "Pinch off yellow bottom leaves"],
                        "water_requirement": "3.5 L/m² daily",
                        "fertilizer_recommendation": "Apply Potassium & Phosphorus top dressing (MOP / Wood ash)",
                        "image_url": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Fruiting",
                        "icon": "🍅",
                        "start_day": 71,
                        "end_day": 95,
                        "description": "Green fruits swell rapidly and start changing color at breaker stage.",
                        "expected_appearance": "Plump green & turning orange tomato clusters hanging heavily from supported vines.",
                        "daily_tasks": ["Monitor for fruit borer holes", "Ensure steady irrigation to prevent fruit cracking", "Support heavy fruit trusses"],
                        "water_requirement": "4.0 L/m² daily",
                        "fertilizer_recommendation": "Foliar spray of Calcium-Boron to prevent blossom end rot",
                        "image_url": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Harvest",
                        "icon": "🧺",
                        "start_day": 96,
                        "end_day": 120,
                        "description": "Fruits reach ripe red stage. Harvest systematically in cool morning hours.",
                        "expected_appearance": "Glossy deep-red mature tomatoes ready for harvesting and marketing.",
                        "daily_tasks": ["Harvest ripe tomatoes at breaker/red stage", "Sort by size into padded crates", "Store in cool shaded shed"],
                        "water_requirement": "Reduce watering to 1.5 L/m² daily to concentrate sugars",
                        "fertilizer_recommendation": "No further fertilizer application required",
                        "image_url": "https://images.unsplash.com/photo-1561136594-7f68413baa99?auto=format&fit=crop&w=600&q=80"
                    }
                ]
            },
            {
                "crop_name": "Chili",
                "variety": "MICO-1 / Waraniya",
                "recommended_season": "Yala & Maha",
                "water_requirements": "Moderate water requirement. Drip irrigation every 2 days. Avoid waterlogging.",
                "fertilizer_guidance": "Basal application of compost (10 t/ha). Top dressing with nitrogen every 3 weeks.",
                "common_problems": "Chili Leaf Curl Virus, Thrips, Anthracnose, Powdery Mildew",
                "basic_solutions": "Yellow sticky traps for thrips, spray neem oil for mildew, rogue infected plants.",
                "image_url": "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80",
                "stages": [
                    {
                        "stage_id": 1,
                        "stage_name": "Nursery Management",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 25,
                        "description": "Raise seedlings under 50% shade net to shield from thrips vectors.",
                        "expected_appearance": "Small green seedlings with 3-4 delicate leaves.",
                        "daily_tasks": ["Water with fine rose shower", "Check for damping off", "Maintain shade net cover"],
                        "water_requirement": "1.0 L/m² daily",
                        "fertilizer_recommendation": "Light bio-fertilizer spray",
                        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Vegetative & Branching",
                        "icon": "🌿",
                        "start_day": 26,
                        "end_day": 50,
                        "description": "Transplant seedlings on ridges. Pinch off first flower bud to encourage bushy branching.",
                        "expected_appearance": "Compact leafy bush with multiple side branches.",
                        "daily_tasks": ["Weed ridges", "Hang yellow sticky traps", "Check tips for leaf curling"],
                        "water_requirement": "2.0 L/m² daily",
                        "fertilizer_recommendation": "Apply Urea (10g/m²) & Neem cake at root zone",
                        "image_url": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Flowering",
                        "icon": "🌸",
                        "start_day": 51,
                        "end_day": 70,
                        "description": "Abundant small white flowers blooming across branches.",
                        "expected_appearance": "Bushy plant covered in white drooping flowers.",
                        "daily_tasks": ["Monitor for flower thrips", "Maintain drip moisture balance", "Apply foliar micronutrients"],
                        "water_requirement": "3.0 L/m² daily",
                        "fertilizer_recommendation": "High Potassium & Boron spray to boost flower hold",
                        "image_url": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Pod Growth & Maturation",
                        "icon": "🌶️",
                        "start_day": 71,
                        "end_day": 95,
                        "description": "Chili pods expand in length and firmness.",
                        "expected_appearance": "Long glossy green chili pods hanging densely from branches.",
                        "daily_tasks": ["Inspect pods for anthracnose spots", "Ensure uniform drip watering", "Staking tall heavy branches"],
                        "water_requirement": "3.0 L/m² daily",
                        "fertilizer_recommendation": "MOP top dressing (15g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Pickings & Harvest",
                        "icon": "🧺",
                        "start_day": 96,
                        "end_day": 120,
                        "description": "Harvest mature green chilies every 5-7 days.",
                        "expected_appearance": "Firm, pungent green or ripening red chilies ready for market.",
                        "daily_tasks": ["Hand-harvest mature pods with pedicel attached", "Spread in ventilated mesh bags", "Avoid harvesting wet pods"],
                        "water_requirement": "2.0 L/m² daily after each picking",
                        "fertilizer_recommendation": "Light Nitrogen top dress after each major picking",
                        "image_url": "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80"
                    }
                ]
            },
            {
                "crop_name": "Eggplant (Brinjal)",
                "variety": "Thinnavelly Purple / Amanda",
                "recommended_season": "Yala & Maha",
                "water_requirements": "High moisture requirement. 3-5 Liters per plant daily during fruiting.",
                "fertilizer_guidance": "Heavy feeder. Apply 15 tons/ha compost as basal plus NPK top dressings.",
                "common_problems": "Shoot and Fruit Borer, Epilachna Beetle, Little Leaf Disease",
                "basic_solutions": "Pheromone traps for shoot borer, clip affected shoots weekly, destroy infected plants.",
                "image_url": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80",
                "stages": [
                    {
                        "stage_id": 1,
                        "stage_name": "Nursery / Seedling",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 25,
                        "description": "Sow seeds in nursery beds. Maintain warm moist soil for healthy germination.",
                        "expected_appearance": "Broad oval green seedlings with sturdy stems.",
                        "daily_tasks": ["Water morning and evening", "Check for flea beetles", "Harden off 3 days before transplanting"],
                        "water_requirement": "1.2 L/m² daily",
                        "fertilizer_recommendation": "Enriched vermicompost basal mix",
                        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Vegetative Branching",
                        "icon": "🌿",
                        "start_day": 26,
                        "end_day": 50,
                        "description": "Transplant at 75cm x 60cm spacing. Develop sturdy framework and large purple-veined leaves.",
                        "expected_appearance": "Tall woody bush with large broad leaves.",
                        "daily_tasks": ["Earthing up soil around base", "Inspect shoots for wilted shoot borer tips", "Apply straw mulch"],
                        "water_requirement": "3.0 L/m² daily",
                        "fertilizer_recommendation": "Urea and MOP top dressing (20g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Flowering & Pollination",
                        "icon": "🌸",
                        "start_day": 51,
                        "end_day": 75,
                        "description": "Purple violet flowers blooming brightly.",
                        "expected_appearance": "Large purple solitary and clustered blossoms with yellow central stamens.",
                        "daily_tasks": ["Clip borer affected shoots", "Install pheromone traps", "Keep root zone moist"],
                        "water_requirement": "4.0 L/m² daily",
                        "fertilizer_recommendation": "Apply organic ash or Potassium sulphate",
                        "image_url": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Fruit Maturation",
                        "icon": "🍆",
                        "start_day": 76,
                        "end_day": 105,
                        "description": "Eggplants swell into glossy purple or striped fruits.",
                        "expected_appearance": "Heavy glossy purple fruits with firm green calyx.",
                        "daily_tasks": ["Inspect fruit skin for borer holes", "Support heavy low branches", "Regular drip irrigation"],
                        "water_requirement": "4.5 L/m² daily",
                        "fertilizer_recommendation": "Foliar micronutrient spray",
                        "image_url": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Harvest",
                        "icon": "🧺",
                        "start_day": 106,
                        "end_day": 130,
                        "description": "Harvest fruits when tender and glossy before seeds harden.",
                        "expected_appearance": "Tender glossy purple brinjals ready for harvesting.",
                        "daily_tasks": ["Cut fruits with sharp secateurs leaving 2cm stem", "Wipe clean with cloth", "Pack in ventilated wooden boxes"],
                        "water_requirement": "3.0 L/m² daily between pickings",
                        "fertilizer_recommendation": "Top-dress compost after every 2 harvest pickings",
                        "image_url": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80"
                    }
                ]
            },
            {
                "crop_name": "Okra",
                "variety": "Haritha / MI-5",
                "recommended_season": "Yala & Maha",
                "water_requirements": "Requires regular moisture. 2-3 Liters per plant daily.",
                "fertilizer_guidance": "Apply basal organic fertilizer. Nitrogen top dressing after 1st picking.",
                "common_problems": "Yellow Vein Mosaic Virus, Powdery Mildew, Fruit Borer",
                "basic_solutions": "Grow YVMV resistant varieties, spray neem oil for whiteflies vector.",
                "image_url": "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80",
                "stages": [
                    {
                        "stage_id": 1,
                        "stage_name": "Germination & Direct Seeding",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 15,
                        "description": "Soak seeds overnight and plant directly in ridges at 60cm x 30cm spacing.",
                        "expected_appearance": "Round heart-shaped green cotyledons emerging from soil.",
                        "daily_tasks": ["Keep seedbed evenly moist", "Thin out double seedlings", "Protect from field ants"],
                        "water_requirement": "1.5 L/m² daily",
                        "fertilizer_recommendation": "Basal compost mixed in ridges",
                        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Vegetative Leaf Growth",
                        "icon": "🌿",
                        "start_day": 16,
                        "end_day": 35,
                        "description": "Rapid stem elongation and development of broad palmate leaves.",
                        "expected_appearance": "Tall erect plant with deeply lobed green leaves.",
                        "daily_tasks": ["Inter-row weeding", "Inspect leaf veins for yellowing (YVMV)", "Earthing up root base"],
                        "water_requirement": "2.5 L/m² daily",
                        "fertilizer_recommendation": "Urea top dressing (15g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Flowering Stage",
                        "icon": "🌸",
                        "start_day": 36,
                        "end_day": 50,
                        "description": "Creamy yellow hibiscus-like flowers with red centers blooming.",
                        "expected_appearance": "Showy pale yellow flowers opening at leaf axils.",
                        "daily_tasks": ["Spray neem oil for whitefly control", "Maintain consistent irrigation", "Check for leaf roller caterpillars"],
                        "water_requirement": "3.5 L/m² daily",
                        "fertilizer_recommendation": "Potassium sulphate foliar spray",
                        "image_url": "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Pod Formation",
                        "icon": "🫛",
                        "start_day": 51,
                        "end_day": 70,
                        "description": "Pods grow rapidly within 4-6 days after flower drop.",
                        "expected_appearance": "Tender ridged green pods pointing upwards.",
                        "daily_tasks": ["Monitor pod growth rate daily", "Ensure water stress is avoided", "Check tips for borer damage"],
                        "water_requirement": "3.5 L/m² daily",
                        "fertilizer_recommendation": "MOP top dress (10g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Pod Harvest",
                        "icon": "🧺",
                        "start_day": 71,
                        "end_day": 90,
                        "description": "Snap tender 8-10cm pods every 2 days before fiber develops.",
                        "expected_appearance": "Crisp tender green pods snapping easily at tip.",
                        "daily_tasks": ["Harvest with gloves/secateurs every alternate day", "Sort out oversized woody pods", "Pack upright in cool bags"],
                        "water_requirement": "2.5 L/m² daily after harvesting",
                        "fertilizer_recommendation": "Urea top dress after every 3 pickings",
                        "image_url": "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80"
                    }
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
                    {
                        "stage_id": 1,
                        "stage_name": "Bulb Planting",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 15,
                        "description": "Plant healthy seed bulbs at 10cm x 15cm spacing in flat beds.",
                        "expected_appearance": "Sprouting green shoots breaking through soil surface.",
                        "daily_tasks": ["Light sprinkler watering", "Keep bed weed-free", "Inspect for root maggots"],
                        "water_requirement": "1.5 L/m² daily",
                        "fertilizer_recommendation": "Basal compost & TSP fertilizer",
                        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Foliar Growth",
                        "icon": "🌿",
                        "start_day": 16,
                        "end_day": 40,
                        "description": "Tubular green leaves multiply rapidly and earth up around base.",
                        "expected_appearance": "Dense stand of dark green tubular onion leaves.",
                        "daily_tasks": ["Manual hand weeding", "Check leaf tips for thrips silvering", "Earthing up soil"],
                        "water_requirement": "2.5 L/m² daily",
                        "fertilizer_recommendation": "Top dressing with Urea (12g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Bulbing Initiation",
                        "icon": "🧅",
                        "start_day": 41,
                        "end_day": 65,
                        "description": "Bulb bases begin expanding under soil surface.",
                        "expected_appearance": "Swelling reddish bulb necks visible above soil line.",
                        "daily_tasks": ["Maintain uniform soil moisture", "Inspect for purple blotch leaf lesions", "Apply sulfur spray if humid"],
                        "water_requirement": "3.0 L/m² daily",
                        "fertilizer_recommendation": "Apply Potassium sulphate (MOP 20g/m²)",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Bulb Swelling",
                        "icon": "🧅",
                        "start_day": 66,
                        "end_day": 85,
                        "description": "Bulbs reach maximum size and skin color turns vibrant red/purple.",
                        "expected_appearance": "Clusters of plump red bulbs exposed at surface.",
                        "daily_tasks": ["Monitor neck softness", "Avoid overhead flooding", "Remove weeds carefully"],
                        "water_requirement": "2.0 L/m² daily",
                        "fertilizer_recommendation": "No more nitrogen fertilizer",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Neck Fall & Curing Harvest",
                        "icon": "🧺",
                        "start_day": 86,
                        "end_day": 100,
                        "description": "Top neck fall (50-70%) signals maturity. Pull bulbs and sun-cure in field.",
                        "expected_appearance": "Dry golden-red bulbs with paper skins and dry tops.",
                        "daily_tasks": ["Stop irrigation completely 7 days before pull", "Pull bulbs and windrow cure in sun 3 days", "Braid tops or store in onion crates"],
                        "water_requirement": "0 L/m² (Dry field)",
                        "fertilizer_recommendation": "None",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"
                    }
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
                    {
                        "stage_id": 1,
                        "stage_name": "Nursery & Land Prep",
                        "icon": "🌱",
                        "start_day": 1,
                        "end_day": 20,
                        "description": "Puddle paddy field thoroughly. Broadcast sprouted seed paddy evenly on wet beds.",
                        "expected_appearance": "Lush green carpet of young paddy sprouts.",
                        "daily_tasks": ["Maintain saturated bed moisture", "Inspect for paddy thrips", "Drain bed overnight"],
                        "water_requirement": "2cm standing water",
                        "fertilizer_recommendation": "Basal TSP & organic compost",
                        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 2,
                        "stage_name": "Tillering Stage",
                        "icon": "🌿",
                        "start_day": 21,
                        "end_day": 50,
                        "description": "Plants produce active tillers and root system expands in standing water.",
                        "expected_appearance": "Dense bushy green hills of paddy tillers.",
                        "daily_tasks": ["Maintain 3-5cm standing water level", "Apply 1st top dressing Urea", "Inspect for dead hearts (stem borer)"],
                        "water_requirement": "5cm standing water",
                        "fertilizer_recommendation": "Urea top dress (30kg/acre)",
                        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 3,
                        "stage_name": "Panicle Initiation",
                        "icon": "🌾",
                        "start_day": 51,
                        "end_day": 75,
                        "description": "Young panicle forms inside stem sheath (booting stage).",
                        "expected_appearance": "Swollen stem boots with dark green canopy.",
                        "daily_tasks": ["Apply 2nd top dress MOP", "Monitor stem base for Brown Planthoppers", "Maintain steady water level"],
                        "water_requirement": "5cm standing water",
                        "fertilizer_recommendation": "MOP top dress (15kg/acre)",
                        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 4,
                        "stage_name": "Flowering & Grain Filling",
                        "icon": "🌸",
                        "start_day": 76,
                        "end_day": 105,
                        "description": "Panicles emerge and anthesis occurs. Milky grains ripen into hard dough.",
                        "expected_appearance": "Exposed panicles arching with milky and hardening grains.",
                        "daily_tasks": ["Check for paddy bug damage", "Maintain shallow water level", "Keep bunds weed-free"],
                        "water_requirement": "3cm standing water",
                        "fertilizer_recommendation": "Foliar Potassium spray if needed",
                        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
                    },
                    {
                        "stage_id": 5,
                        "stage_name": "Golden Harvest",
                        "icon": "🧺",
                        "start_day": 106,
                        "end_day": 125,
                        "description": "85% of panicles turn golden yellow. Drain field 10 days before harvesting.",
                        "expected_appearance": "Golden yellow field of heavy drooping grain heads.",
                        "daily_tasks": ["Drain paddy field completely", "Combine harvest or hand sickle cut", "Thresh and sun-dry paddy grains to 14% moisture"],
                        "water_requirement": "Drain field completely",
                        "fertilizer_recommendation": "None",
                        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
                    }
                ]
            }
        ]

        for g_data in guides_data:
            stages = g_data.pop("stages")
            guide = CropGuide.query.filter_by(crop_name=g_data["crop_name"]).first()
            if not guide:
                guide = CropGuide(**g_data)
                guide.set_growth_stages(stages)
                db.session.add(guide)
            else:
                for k, v in g_data.items():
                    setattr(guide, k, v)
                guide.set_growth_stages(stages)

        db.session.commit()
        print(f"Seeded/Updated {len(guides_data)} crop guides with complete 5-stage lifecycles.")


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
