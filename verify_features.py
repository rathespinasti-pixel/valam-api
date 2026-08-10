import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.crop_guide import CropGuide

app = create_app("development")

with app.app_context():
    # 1. Test Admin Login
    with app.test_client() as client:
        admin_login = client.post("/api/auth/login", json={
            "email": "admin@gmail.com",
            "password": "Admin@1234"
        })
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.get_json()}"
        admin_token = admin_login.get_json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}", "Origin": "http://localhost:3000"}

        # 2. Test Create Farmer User
        test_email = "testfarmer@valam.lk"
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        create_res = client.post("/api/admin/users", json={
            "full_name": "Test Farmer Vavuniya",
            "email": test_email,
            "password": "Farmer@1234",
            "phone": "0771122334",
            "farming_category": "Farmer",
            "district": "Vavuniya"
        }, headers=headers)
        assert create_res.status_code == 201, f"Create user failed: {create_res.get_json()}"
        user_id = create_res.get_json()["data"]["id"]
        print(f"PASS: Created farmer #{user_id} ({test_email})")

        # 3. Test Ban User with Reason
        ban_reason = "Spamming agricultural tool listings with false pricing"
        ban_res = client.put(f"/api/admin/users/{user_id}/ban", json={
            "status": "banned",
            "reason": ban_reason
        }, headers=headers)
        assert ban_res.status_code == 200, f"Ban failed: {ban_res.get_json()}"
        banned_user = ban_res.get_json()["data"]
        assert banned_user["status"] == "banned"
        assert banned_user["ban_reason"] == ban_reason
        print(f"PASS: Banned user with reason: '{banned_user['ban_reason']}'")

        # 4. Test Banned User Login Attempt
        banned_login = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "Farmer@1234"
        })
        assert banned_login.status_code == 403, f"Expected 403, got {banned_login.status_code}: {banned_login.get_json()}"
        err_msg = banned_login.get_json()["message"]
        assert ban_reason in err_msg, f"Ban reason not in error message: {err_msg}"
        print(f"PASS: Banned login rejected with message: '{err_msg}'")

        # 5. Test Unban User
        unban_res = client.put(f"/api/admin/users/{user_id}/ban", json={
            "status": "active"
        }, headers=headers)
        assert unban_res.status_code == 200
        unbanned_user = unban_res.get_json()["data"]
        assert unbanned_user["status"] == "active"
        assert unbanned_user["ban_reason"] is None
        print("PASS: User unbanned successfully")

        # 6. Test Unbanned User Login Attempt
        active_login = client.post("/api/auth/login", json={
            "email": test_email,
            "password": "Farmer@1234"
        })
        assert active_login.status_code == 200, f"Login failed after unban: {active_login.get_json()}"
        print("PASS: Unbanned farmer logged in successfully")

        # 7. Test Admin Crop Guide with Planting Method and Stage Compost
        guide_res = client.post("/api/crop-guides", json={
            "crop_name": "Test Maize",
            "variety": "Ruwan Hybrid",
            "recommended_season": "Yala & Maha",
            "planting_method": "Direct Seeding",
            "fertilizer_type": "Organic",
            "water_requirements": "4.0 L/m² daily",
            "stage_composts": [
                {
                    "stage_name": "Basal Land Prep",
                    "days_range": "Days 0-14",
                    "compost_type": "Organic",
                    "recommended_compost": "Decomposed Cow Dung 10 tons/acre + 50kg Neem Cake",
                    "dosage": "10 tons/acre",
                    "application_method": "Broadcast into soil"
                },
                {
                    "stage_name": "Vegetative Stage",
                    "days_range": "Days 15-35",
                    "compost_type": "Organic",
                    "recommended_compost": "Vermicompost top dressing",
                    "dosage": "500 kg/acre",
                    "application_method": "Row side dressing"
                }
            ]
        }, headers=headers)
        assert guide_res.status_code == 201, f"Crop guide failed: {guide_res.get_json()}"
        guide_data = guide_res.get_json()["data"]
        assert guide_data["planting_method"] == "Direct Seeding"
        assert len(guide_data["stage_composts"]) == 2
        print(f"PASS: Created Crop Guide with stage composts: {guide_data['crop_name']}")

        # 8. Test AI Direct Seeding Calculation
        ai_res = client.post("/api/chatbot/ask", json={
            "question": "I have 1 acre land for direct seeding Maize. How much seed should I buy and what drip length is needed?",
            "language": "en"
        }, headers=headers)
        assert ai_res.status_code == 200, f"AI ask failed: {ai_res.get_json()}"
        ai_answer = ai_res.get_json()["data"]["answer"]
        print(f"PASS: AI Chatbot Answer generated:\n---\n{ai_answer[:300]}...\n---")

        # Clean up test user & crop guide
        db.session.delete(User.query.get(user_id))
        db.session.delete(CropGuide.query.get(guide_data["id"]))
        db.session.commit()
        print("ALL BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
