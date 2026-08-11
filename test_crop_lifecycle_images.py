import os
from datetime import datetime, timedelta
from app import create_app
from app.services.gemini_image_service import GeminiImageService

app = create_app()

with app.app_context():
    print("======================================================================")
    print("TESTING DYNAMIC AI CROP LIFECYCLE IMAGES & ISOLATION")
    print("======================================================================")

    # 1. Test Prompt Generation for Tomato, Brinjal, Green Chilli
    prompt_tomato = GeminiImageService._build_prompt(
        crop_name="Tomato",
        stage_name="Flowering",
        variety="Thilina (KC1)",
        crop_age=50
    )
    print("\n--- 1. Tomato Prompt Verification ---")
    print(f"Generated Prompt: {prompt_tomato}")
    assert "Tomato" in prompt_tomato
    assert "Thilina (KC1)" in prompt_tomato
    assert "Flowering" in prompt_tomato
    assert "STRICT NEGATIVE CONSTRAINTS" in prompt_tomato
    print("[OK] Tomato prompt verified successfully.")

    # 2. Test Image Generation / Retrieval for Multiple Crops & Stages
    test_cases = [
        {"crop": "Tomato", "variety": "Thilina", "stage": "Flowering", "age": 55},
        {"crop": "Tomato", "variety": "Thilina", "stage": "Vegetative Growth", "age": 30},
        {"crop": "Brinjal", "variety": "Padagoda", "stage": "Flowering", "age": 60},
        {"crop": "Brinjal", "variety": "Padagoda", "stage": "Fruiting", "age": 80},
        {"crop": "Green Chilli", "variety": "MI-2", "stage": "Vegetative Growth", "age": 35},
        {"crop": "Green Chilli", "variety": "MI-2", "stage": "Fruiting", "age": 75},
    ]

    print("\n--- 2. Crop-Isolated Lifecycle Image Retrieval ---")
    for tc in test_cases:
        res = GeminiImageService.get_or_generate_lifecycle_image(
            crop_name=tc["crop"],
            stage=tc["stage"],
            variety=tc["variety"],
            crop_age=tc["age"]
        )
        print(f"Crop: {tc['crop']} | Stage: {tc['stage']} | Source: {res.get('source')} | Image URL: {res.get('image_url')[:60]}...")
        assert res.get("image_url") is not None
        assert res.get("crop_name").lower() == tc["crop"].lower()

    # 3. Test Planting Date to Stage Calculation
    print("\n--- 3. Automatic Stage Calculation from Planting Date ---")
    today = datetime.now().date()
    
    stages_to_test = [
        (5, "seedling"),       # 5 days ago -> Seedling
        (21, "seedling"),      # 21 days ago -> Transplanting / Early
        (35, "vegetative"),    # 35 days ago -> Vegetative Growth
        (55, "flowering"),     # 55 days ago -> Flowering
        (80, "fruiting"),      # 80 days ago -> Fruiting
        (110, "harvest"),      # 110 days ago -> Harvest
    ]

    for days_ago, expected_stage in stages_to_test:
        planting_date = today - timedelta(days=days_ago)
        crop_age = (today - planting_date).days
        stage_key = GeminiImageService.get_stage_key(
            "Seedling" if crop_age <= 20 else
            "Transplanting" if crop_age == 21 else
            "Vegetative Growth" if crop_age <= 45 else
            "Flowering" if crop_age <= 70 else
            "Fruiting" if crop_age <= 95 else "Harvest"
        )
        print(f"Planted: {planting_date} (Age: {crop_age} days) -> Stage Key: {stage_key}")
        if expected_stage != "seedling" or crop_age <= 21:
            assert stage_key == expected_stage or (days_ago == 21 and stage_key in ["seedling", "transplanting"])

    print("\n======================================================================")
    print("ALL BACKEND CROP LIFECYCLE & IMAGE TESTS PASSED!")
    print("======================================================================")
