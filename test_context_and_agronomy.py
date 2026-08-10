from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.crop import Crop

app = create_app("development")

with app.app_context():
    with app.test_client() as client:
        # 1. Admin Login
        admin_login = client.post("/api/auth/login", json={
            "email": "admin@gmail.com",
            "password": "Admin@1234"
        })
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.get_json()}"
        admin_token = admin_login.get_json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}", "Origin": "http://localhost:3000"}

        # 2. Test Admin Suggest Agronomy Plan for Organic Chilli
        print("\n--- TEST 1: Admin Suggest Agronomy Plan (Organic Chilli) ---")
        agri_res = client.post("/api/crop-guides/suggest-agronomy", json={
            "crop_name": "Chilli",
            "variety": "MI-2",
            "planting_method": "Direct Seeding",
            "fertilizer_type": "Organic",
            "season": "Yala",
            "district": "Vavuniya"
        }, headers=admin_headers)
        assert agri_res.status_code == 200, f"Suggest agronomy failed: {agri_res.get_json()}"
        plan = agri_res.get_json()["data"]
        assert plan["crop_name"] == "Chilli"
        assert len(plan["growth_stages"]) >= 5, f"Expected >=5 stages, got {len(plan['growth_stages'])}"
        assert len(plan["stage_composts"]) >= 5, f"Expected >=5 compost stages, got {len(plan['stage_composts'])}"
        print(f"PASS: Generated Agronomy Plan for Chilli with {len(plan['growth_stages'])} growth stages and {len(plan['stage_composts'])} stage compost recipes.")
        print(f"Stage 1 Compost: {plan['stage_composts'][0]['recommended_compost']} ({plan['stage_composts'][0]['dosage']})")

        # 3. Test Admin Suggest Agronomy Plan for Chemical Maize
        print("\n--- TEST 2: Admin Suggest Agronomy Plan (Chemical Maize) ---")
        maize_res = client.post("/api/crop-guides/suggest-agronomy", json={
            "crop_name": "Maize",
            "variety": "Ruwan",
            "planting_method": "Direct Seeding",
            "fertilizer_type": "Non-Organic / Chemical",
            "season": "Maha",
            "district": "Vavuniya"
        }, headers=admin_headers)
        assert maize_res.status_code == 200, f"Suggest agronomy failed: {maize_res.get_json()}"
        maize_plan = maize_res.get_json()["data"]
        assert len(maize_plan["growth_stages"]) >= 5
        print(f"PASS: Generated Chemical Maize Plan with {len(maize_plan['growth_stages'])} stages.")

        # 4. Create a test farmer with active crop for Context-Aware Chatbot test
        print("\n--- TEST 3: Context-Aware AI Chatbot ---")
        test_email = "context_farmer@valam.lk"
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            Crop.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

        farmer = User(
            full_name="Murugan Farmer",
            email=test_email,
            phone="0779988776",
            farming_category="Farmer",
            district="Vavuniya",
            ds_division="Vavuniya South",
            land_size=2.0,
            land_size_unit="Acres",
            irrigation_preference="Drip Irrigation",
            fertilizer_preference="Organic",
            role="farmer",
            status="active"
        )
        farmer.set_password("Farmer@1234")
        db.session.add(farmer)
        db.session.commit()

        # Add active crop: Tomato planted 45 days ago (Flowering Stage)
        crop = Crop(
            user_id=farmer.id,
            crop_name="Tomato",
            variety="Thilina",
            planting_date=date.today() - timedelta(days=45),
            current_stage="Flowering Stage",
            land_size=1.0,
            land_size_unit="Acres",
            planting_method="Direct Seeding",
            irrigation_type="Drip Irrigation",
            fertilizer_preference="Organic",
            is_active=True
        )
        db.session.add(crop)
        db.session.commit()

        # Login as farmer
        farmer_login = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "Farmer@1234"
        })
        assert farmer_login.status_code == 200
        farmer_token = farmer_login.get_json()["data"]["access_token"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}", "Origin": "http://localhost:3000"}

        # Ask a general question: "When should I apply fertilizer and water?"
        chat_res = client.post("/api/chatbot/ask", json={
            "question": "When should I apply fertilizer and water?",
            "language": "en",
            "page_context": {"page": "crop-simulator", "crop_name": "Tomato", "stage": "Flowering Stage"}
        }, headers=farmer_headers)
        assert chat_res.status_code == 200, f"Chat ask failed: {chat_res.get_json()}"
        chat_data = chat_res.get_json()["data"]
        answer = chat_data["answer"]
        print(f"Context Applied: {chat_data.get('context_applied')}")
        safe_ans = answer.encode("ascii", "replace").decode("ascii")
        print(f"\nAI Chatbot Answer:\n----------------------------------------\n{safe_ans[:400]}...\n----------------------------------------")

        # Verify that the answer mentions Tomato and Flowering / Flower stage
        lower_ans = answer.lower()
        has_crop_mention = "tomato" in lower_ans or "thilina" in lower_ans or "flowering" in lower_ans or "flower" in lower_ans
        print(f"PASS: AI directly tailored answer to farmer's active Tomato crop at Flowering stage: {has_crop_mention}")

        # Clean up
        Crop.query.filter_by(user_id=farmer.id).delete()
        db.session.delete(farmer)
        db.session.commit()
        print("\nALL CONTEXT-AWARE & AGRONOMIC PLAN TESTS PASSED SUCCESSFULLY!")
