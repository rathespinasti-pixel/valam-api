import json
import logging
import re
from app.services.perenual_service import PerenualService
from app.services.gemini_service import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)

# Curated reference agronomic knowledge base for primary dry zone crops in Sri Lanka
AGRONOMIC_KNOWLEDGE_PRESETS = {
    "tomato": {
        "scientific_name": "Solanum lycopersicum",
        "total_days": 105,
        "water_requirements": "3.5 - 4.5 L/m² daily via drip",
        "irrigation_method": "Drip Irrigation with 40cm emitter spacing (approx. 4,000m lateral/acre)",
        "fertilizer_guidance": "Basal compost with high organic matter followed by balanced potassium-rich top dressings during flowering and fruiting.",
        "common_problems": "Bacterial Wilt (Ralstonia), Early Blight (Alternaria solani), Whiteflies, Fruit Borer (Helicoverpa)",
        "basic_solutions": "Use resistant varieties (e.g., Thilina, Padparadscha), spray 5% Neem Seed Kernel Extract (NSKE), Trichoderma soil drench, and avoid waterlogging.",
        "stages": [
            {
                "stage_id": 1,
                "stage_name": "1. Basal / Land Prep & Sowing",
                "icon": "🌱",
                "start_day": 0,
                "end_day": 15,
                "description": "Deep ploughing, raised bed formation (1m width), incorporation of basal compost, and direct seed placement (2-3 seeds per hill) or nursery raising.",
                "expected_appearance": "Moist raised seedbeds with emerging green cotyledons by day 6-8.",
                "water_requirement": "Light daily moisture (2.0 - 2.5 L/m²)",
                "fertilizer_recommendation": "Well-decomposed cow dung 8-10 tons/acre + 50kg Neem cake incorporated into topsoil.",
                "daily_tasks": ["Raised bed preparation", "Trichoderma soil treatment", "Seed sowing at 2cm depth", "Gentle morning misting"]
            },
            {
                "stage_id": 2,
                "stage_name": "2. Vegetative Growth & Staking",
                "icon": "🌿",
                "start_day": 16,
                "end_day": 35,
                "description": "Thinning to single vigorous plant, staking installation, and side dressing of organic/inorganic nutrients.",
                "expected_appearance": "Sturdy central stalk with 6-10 deep green branching leaves.",
                "water_requirement": "Drip watering every 2 days (3.0 - 3.5 L/m²)",
                "fertilizer_recommendation": "Vermicompost top dressing (500 kg/acre) + Jeevamrutham 3% liquid foliar spray.",
                "daily_tasks": ["Thinning surplus shoots", "Staking with bamboo poles", "Earthing up root zones", "Weeding"]
            },
            {
                "stage_id": 3,
                "stage_name": "3. Flowering Cluster Stage",
                "icon": "🌼",
                "start_day": 36,
                "end_day": 55,
                "description": "First blossom clusters open; high demand for phosphorus, calcium, and boron.",
                "expected_appearance": "Abundant bright yellow blossom clusters opening along branches.",
                "water_requirement": "Steady moisture (3.5 - 4.0 L/m²). Avoid water stress to prevent flower drop.",
                "fertilizer_recommendation": "Wood ash + Sterilized bone meal (100 kg/acre) or NPK 1:2:1 ring placed 10cm from base.",
                "daily_tasks": ["Blossom inspection", "Neem oil spray for whiteflies", "Mulch top-up", "Monitor drip uniformity"]
            },
            {
                "stage_id": 4,
                "stage_name": "4. Fruit Set & Berry Expansion",
                "icon": "🍅",
                "start_day": 56,
                "end_day": 80,
                "description": "Rapid fruit swelling and green berry development. High potassium requirement.",
                "expected_appearance": "Heavy clusters of firm green swelling fruits hanging from supported vines.",
                "water_requirement": "Peak demand: 4.5 - 5.0 L/m² daily in dry zone sunshine.",
                "fertilizer_recommendation": "Fermented compost tea / Liquid seaweed bio-extract applied through drip line.",
                "daily_tasks": ["Lower leaf pruning for aeration", "Fruit borer pheromone traps", "Maintaining fertigation", "Checking fruit supports"]
            },
            {
                "stage_id": 5,
                "stage_name": "5. Fruit Ripening & Harvest",
                "icon": "🧺",
                "start_day": 81,
                "end_day": 105,
                "description": "Breaker stage turning from pink to uniform deep red. Multi-pick harvesting every 3-4 days.",
                "expected_appearance": "Glossy ripe red fruits ready for gentle hand picking.",
                "water_requirement": "Moderate (3.0 L/m²); taper off 3 days before picking to concentrate sugar content.",
                "fertilizer_recommendation": "Maintain dry paddy straw mulch to prevent soil-splash pathogens.",
                "daily_tasks": ["Morning harvesting into crates", "Grading and sorting", "Post-harvest shading", "Vine maintenance"]
            }
        ],
        "composts": [
            {
                "stage_name": "1. Basal / Land Preparation & Sowing",
                "days_range": "Days 0 - 15",
                "compost_type": "Organic",
                "recommended_compost": "Decomposed Cow Dung / Farmyard Manure (8-10 tons/acre) + 50kg Neem Cake",
                "dosage": "8-10 tons / acre",
                "application_method": "Incorporate thoroughly into top 15cm soil during primary bed formation",
                "water_tips": "Moisten soil lightly 2 days prior to direct seed sowing"
            },
            {
                "stage_name": "2. Vegetative Growth Stage",
                "days_range": "Days 16 - 35",
                "compost_type": "Organic",
                "recommended_compost": "Vermicompost top dressing + Jeevamrutham 3% foliar spray",
                "dosage": "500 kg / acre vermicompost",
                "application_method": "Side dress along crop rows followed by light earthing up",
                "water_tips": "Drip irrigation every 2 days (3.0 - 3.5 L/m²)"
            },
            {
                "stage_name": "3. Flowering Stage",
                "days_range": "Days 36 - 55",
                "compost_type": "Organic",
                "recommended_compost": "Sterilized Bone Meal + Wood Ash (rich in Phosphorus & Potassium)",
                "dosage": "100 kg / acre",
                "application_method": "Ring placement 10cm away from base stem and covered with mulch",
                "water_tips": "Maintain steady moisture; avoid over-head spraying to protect blossoms"
            },
            {
                "stage_name": "4. Fruit Set & Expansion",
                "days_range": "Days 56 - 80",
                "compost_type": "Organic",
                "recommended_compost": "Potassium-rich organic compost tea / Fermented fruit juice (FFJ)",
                "dosage": "200 L liquid tea / acre",
                "application_method": "Applied via drip fertigation or soil root drenching",
                "water_tips": "Peak watering: 4.5 - 5.0 L/m² daily in dry season"
            },
            {
                "stage_name": "5. Harvesting & Maturity",
                "days_range": "Days 81 - 105",
                "compost_type": "Organic",
                "recommended_compost": "Dry organic mulch maintenance (paddy straw / dried leaves)",
                "dosage": "2-3 inch mulch layer",
                "application_method": "Surface spread across furrows",
                "water_tips": "Reduce irrigation 3-4 days before picking for higher flavor concentration"
            }
        ]
    },
    "chilli": {
        "scientific_name": "Capsicum annuum",
        "total_days": 135,
        "water_requirements": "3.0 - 4.0 L/m² daily",
        "irrigation_method": "Drip irrigation (4,000m lateral/acre, 30cm emitter spacing)",
        "fertilizer_guidance": "High organic matter basal with supplementary nitrogen at vegetative stage and potassium during pod setting.",
        "common_problems": "Chilli Leaf Curl Virus (Gemini virus transmitted by whiteflies/thrips), Anthracnose, Mites, Damping-off",
        "basic_solutions": "Grow tolerant varieties (MI-2, Waraniya), spray 5% Neem Seed Kernel Extract + Soap solution, yellow/blue sticky traps, sulfur for mites.",
        "stages": [
            {"stage_id": 1, "stage_name": "1. Basal Land Prep & Sowing", "icon": "🌱", "start_day": 0, "end_day": 20, "description": "Bed formation and direct seeding or nursery sowing with organic basal manure.", "expected_appearance": "Fine seedbeds with two-leaf cotyledons emerging.", "water_requirement": "2.0 L/m² light daily", "fertilizer_recommendation": "10 tons well-decomposed manure + 50kg Neem cake/acre.", "daily_tasks": ["Raised bed prep", "Seed sowing", "Mist watering"]},
            {"stage_id": 2, "stage_name": "2. Vegetative Branching Stage", "icon": "🌿", "start_day": 21, "end_day": 45, "description": "Strong canopy development and secondary branching.", "expected_appearance": "Vigorous bush with 12-18 dark green leaves.", "water_requirement": "3.0 L/m² every 2 days", "fertilizer_recommendation": "Vermicompost 600kg/acre + Panchagavya 3% spray.", "daily_tasks": ["Weeding", "Pest monitoring for thrips", "Earthing up"]},
            {"stage_id": 3, "stage_name": "3. Flower Bud & Anthesis", "icon": "🌼", "start_day": 46, "end_day": 70, "description": "First star-shaped white flowers emerge at stem forks.", "expected_appearance": "Dense white blossoms across branch nodes.", "water_requirement": "3.5 L/m² steady moisture", "fertilizer_recommendation": "Bone meal 120kg/acre + Wood ash.", "daily_tasks": ["Whitefly & mite inspection", "Foliar boron spray", "Mulching"]},
            {"stage_id": 4, "stage_name": "4. Pod Elongation & Pungency", "icon": "🌶️", "start_day": 71, "end_day": 105, "description": "Rapid pod elongation, firming, and capsaicin accumulation.", "expected_appearance": "Heavy clusters of glossy green pendent pods.", "water_requirement": "4.0 L/m² daily", "fertilizer_recommendation": "Liquid compost tea fertigation + Potassium wash.", "daily_tasks": ["Anthracnose prevention", "Drip fertigation", "Staking tall bushes"]},
            {"stage_id": 5, "stage_name": "5. Green / Red Ripe Picking", "icon": "🧺", "start_day": 106, "end_day": 135, "description": "Continuous harvesting of green chillies or mature red chillies every 5-7 days.", "expected_appearance": "Vibrant green or fiery red mature pods ready for harvest.", "water_requirement": "2.5 - 3.0 L/m²", "fertilizer_recommendation": "Light organic maintenance top-dress after each major flush.", "daily_tasks": ["Selective harvesting", "Drying on mats (for red chilli)", "Post-harvest cleaning"]}
        ],
        "composts": [
            {"stage_name": "1. Basal Land Preparation", "days_range": "Days 0 - 20", "compost_type": "Organic", "recommended_compost": "Decomposed Farmyard Manure 10 tons/acre + 50kg Neem Cake", "dosage": "10 tons / acre", "application_method": "Thoroughly mixed into topsoil", "water_tips": "Moist soil before sowing"},
            {"stage_name": "2. Vegetative Branching", "days_range": "Days 21 - 45", "compost_type": "Organic", "recommended_compost": "Vermicompost + Panchagavya 3% spray", "dosage": "600 kg / acre", "application_method": "Row side dressing & foliar spray", "water_tips": "Drip every 2 days"},
            {"stage_name": "3. Flowering Stage", "days_range": "Days 46 - 70", "compost_type": "Organic", "recommended_compost": "Bone meal + Wood ash ring placement", "dosage": "120 kg / acre", "application_method": "Ring placement 10cm from base", "water_tips": "Consistent moisture to prevent flower drop"},
            {"stage_name": "4. Pod Formation Stage", "days_range": "Days 71 - 105", "compost_type": "Organic", "recommended_compost": "Fermented compost tea / Liquid bio-extract", "dosage": "250 L / acre", "application_method": "Drip fertigation line", "water_tips": "Peak water demand"},
            {"stage_name": "5. Harvesting Stage", "days_range": "Days 106 - 135", "compost_type": "Organic", "recommended_compost": "Organic compost maintenance after each picking flush", "dosage": "200 kg / acre", "application_method": "Surface dressing between rows", "water_tips": "Water moderately after each picking"}
        ]
    },
    "maize": {
        "scientific_name": "Zea mays",
        "total_days": 105,
        "water_requirements": "4.0 - 5.0 L/m² daily",
        "irrigation_method": "Drip / Furrow irrigation (row spacing 60cm x plant spacing 25cm)",
        "fertilizer_guidance": "High nitrogen & phosphorus demand during knee-high and tasseling stages.",
        "common_problems": "Fall Armyworm (Spodoptera frugiperda), Stem Borer, Downy Mildew",
        "basic_solutions": "Direct seed treatment with bio-fungicide, apply sand/neem seed powder into leaf whorls for armyworm, pheromone traps.",
        "stages": [
            {"stage_id": 1, "stage_name": "1. Basal Soil Prep & Direct Seeding", "icon": "🌱", "start_day": 0, "end_day": 14, "description": "Primary ploughing, ridge formation, and direct seed dibbling at 8-10 kg/acre.", "expected_appearance": "Erect coleoptile shoots emerging through moist furrows by day 4-6.", "water_requirement": "2.5 L/m²", "fertilizer_recommendation": "8 tons cow manure + 50kg Neem cake basal.", "daily_tasks": ["Ridge preparation", "Direct dibbling at 3cm depth", "Pre-emergence watering"]},
            {"stage_id": 2, "stage_name": "2. Knee-High Vegetative Stage", "icon": "🌿", "start_day": 15, "end_day": 35, "description": "Rapid stalk elongation (V6 stage) and deep root anchoring.", "expected_appearance": "Sturdy green stalks reaching knee height with broad leaves.", "water_requirement": "3.5 L/m²", "fertilizer_recommendation": "Vermicompost top dressing (800kg/acre) or Urea 50kg/acre.", "daily_tasks": ["Armyworm whorl inspection", "Earthing up ridges", "Weeding"]},
            {"stage_id": 3, "stage_name": "3. Tasseling & Silking Stage", "icon": "🌽", "start_day": 36, "end_day": 60, "description": "Tassel emergence shedding pollen onto female ear silks. Critical water stage.", "expected_appearance": "Golden tassels on top with silky pink ear shoots at middle nodes.", "water_requirement": "5.0 L/m² peak moisture (zero drought stress allowed)", "fertilizer_recommendation": "Potassium-rich organic wash / MOP top dress.", "daily_tasks": ["Ensure uninterrupted drip irrigation", "Ear protection", "Windbreak monitoring"]},
            {"stage_id": 4, "stage_name": "4. Grain Filling & Milk/Dough Stage", "icon": "🌾", "start_day": 61, "end_day": 85, "description": "Kernels swelling and storing starch in dense cobs.", "expected_appearance": "Heavy plump cobs with darkening dry silks.", "water_requirement": "4.0 L/m²", "fertilizer_recommendation": "Bio-potash foliar spray.", "daily_tasks": ["Cob borer monitoring", "Bird scaring", "Moisture maintenance"]},
            {"stage_id": 5, "stage_name": "5. Black Layer Maturity & Harvest", "icon": "🧺", "start_day": 86, "end_day": 105, "description": "Husk drying to straw-yellow; kernels reach physiological maturity.", "expected_appearance": "Dry golden cobs hanging downward ready for snapping.", "water_requirement": "Zero watering 7-10 days before harvest.", "fertilizer_recommendation": "None (maturity reached).", "daily_tasks": ["Cob harvesting", "De-husking and sun drying", "Grain moisture testing (14%)"]}
        ],
        "composts": [
            {"stage_name": "1. Basal Land Preparation", "days_range": "Days 0 - 14", "compost_type": "Organic", "recommended_compost": "Decomposed Cattle Manure 8 tons/acre + 50kg Neem Cake", "dosage": "8 tons / acre", "application_method": "Furrow incorporation during ploughing", "water_tips": "Irrigate immediately after direct sowing"},
            {"stage_name": "2. Knee-High Stage", "days_range": "Days 15 - 35", "compost_type": "Organic", "recommended_compost": "Vermicompost top dressing + Jeevamrutham", "dosage": "800 kg / acre", "application_method": "Side dress along rows followed by earthing up", "water_tips": "Water every 3 days"},
            {"stage_name": "3. Tasseling & Silking", "days_range": "Days 36 - 60", "compost_type": "Organic", "recommended_compost": "Wood ash + Bone meal (high Phosphorus & Potassium)", "dosage": "150 kg / acre", "application_method": "Ring broadcast along furrows", "water_tips": "Critical: Never allow water stress"},
            {"stage_name": "4. Grain Filling", "days_range": "Days 61 - 85", "compost_type": "Organic", "recommended_compost": "Liquid fermented compost tea", "dosage": "300 L / acre", "application_method": "Drip fertigation", "water_tips": "Maintain regular watering"},
            {"stage_name": "5. Harvesting Stage", "days_range": "Days 86 - 105", "compost_type": "Organic", "recommended_compost": "Post-harvest crop residue incorporation for soil health", "dosage": "Shredded stalks", "application_method": "Ploughed back into soil", "water_tips": "Stop watering 10 days before harvest"}
        ]
    }
}


class AgronomyEngineService:
    """Intelligent Agricultural Recommendation Engine combining Botanical APIs, AI, and verified agronomical guidelines."""

    @classmethod
    def suggest_crop_plan(
        cls,
        crop_name: str,
        variety: str = "Standard",
        planting_method: str = "Direct Seeding",
        fertilizer_type: str = "Organic",
        season: str = "Yala & Maha",
        district: str = "Vavuniya"
    ) -> dict:
        clean_crop = (crop_name or "Tomato").strip()
        clean_key = clean_crop.lower()

        # Step 1: Query Perenual Botanical Database
        botanical_info = {}
        try:
            botanical_info = PerenualService.get_plant_info(clean_crop)
        except Exception as e:
            logger.warning(f"Botanical info lookup failed: {e}")

        # Step 2: Check for Gemini AI generation with structured JSON schema
        prompt = f"""
You are an expert Agronomist and Senior Agricultural Officer at the Department of Agriculture, Sri Lanka.
Generate a complete, scientifically accurate, and non-generic Agronomic Cultivation Plan for the following crop:

Target Crop: {clean_crop}
Variety: {variety or 'Standard adapted to Sri Lanka dry zone'}
Planting Method: {planting_method} (e.g. Direct Seeding or Transplanting)
Fertilizer Preference: {fertilizer_type} (Organic, Non-Organic / Chemical, or Integrated)
Growing Season: {season}
Location: {district}, Northern/North-Central Dry Zone, Sri Lanka

Botanical Reference:
Scientific Name: {botanical_info.get('scientific_name', 'Botanical standard')}
Family: {botanical_info.get('family', 'Agricultural')}
Water Requirement: {botanical_info.get('water_requirement', 'Standard')}
Soil Preference: {botanical_info.get('soil_preference', 'Well-drained loam')}

REQUIREMENTS:
1. Provide precise growth duration in days tailored to {clean_crop}.
2. Provide exact daily water requirement (L/m² daily) and irrigation layout (drip lateral length, emitter spacing).
3. Provide realistic common pests & diseases in Sri Lanka and actionable organic + chemical management.
4. Provide a 5-stage lifecycle breakdown ({clean_crop} growth stages) with exact start_day and end_day, descriptions, water requirements, and daily tasks.
5. Provide a 5-stage compost & fertilizer schedule tailored specifically to {fertilizer_type} ({'Focus on Farmyard Manure, Vermicompost, Neem Cake, Panchagavya, Jeevamrutham, Bone meal' if 'Organic' in fertilizer_type else 'Focus on NPK ratios, Urea, TSP, MOP, basal and top dressing schedules'}) and {planting_method}.

CRITICAL: Return ONLY valid JSON matching this exact structure without markdown or backticks:
{{
  "crop_name": "{clean_crop}",
  "variety": "{variety}",
  "total_days": 105,
  "planting_method": "{planting_method}",
  "fertilizer_type": "{fertilizer_type}",
  "recommended_season": "{season}",
  "water_requirements": "3.5 - 4.5 L/m² daily via drip",
  "irrigation_method": "Drip Irrigation with 40cm emitter spacing (4,000m lateral/acre)",
  "fertilizer_guidance": "Detailed fertilizer overview for {fertilizer_type} management",
  "common_problems": "Pest 1, Disease 2, Pest 3",
  "basic_solutions": "Specific treatment steps for Sri Lanka conditions",
  "growth_stages": [
    {{
      "stage_id": 1,
      "stage_name": "1. Basal / Land Prep & Sowing",
      "icon": "🌱",
      "start_day": 0,
      "end_day": 15,
      "description": "Clear step description",
      "expected_appearance": "Visual look of plant",
      "water_requirement": "2.0 L/m² daily",
      "fertilizer_recommendation": "Exact basal recipe",
      "daily_tasks": ["Task 1", "Task 2", "Task 3"]
    }},
    {{
      "stage_id": 2,
      "stage_name": "2. Vegetative Growth Stage",
      "icon": "🌿",
      "start_day": 16,
      "end_day": 35,
      "description": "Vegetative phase description",
      "expected_appearance": "Visual look",
      "water_requirement": "3.5 L/m² every 2 days",
      "fertilizer_recommendation": "Top dressing recipe",
      "daily_tasks": ["Task 1", "Task 2"]
    }},
    {{
      "stage_id": 3,
      "stage_name": "3. Flowering Stage",
      "icon": "🌼",
      "start_day": 36,
      "end_day": 55,
      "description": "Flowering details",
      "expected_appearance": "Visual look",
      "water_requirement": "4.0 L/m²",
      "fertilizer_recommendation": "Phosphorus & potassium recipe",
      "daily_tasks": ["Task 1", "Task 2"]
    }},
    {{
      "stage_id": 4,
      "stage_name": "4. Fruit / Pod Development",
      "icon": "🍅",
      "start_day": 56,
      "end_day": 80,
      "description": "Fruit sizing details",
      "expected_appearance": "Visual look",
      "water_requirement": "4.5 L/m²",
      "fertilizer_recommendation": "Fruiting nutrient recipe",
      "daily_tasks": ["Task 1", "Task 2"]
    }},
    {{
      "stage_id": 5,
      "stage_name": "5. Harvesting & Maturity",
      "icon": "🧺",
      "start_day": 81,
      "end_day": 105,
      "description": "Harvest details",
      "expected_appearance": "Visual look",
      "water_requirement": "3.0 L/m²",
      "fertilizer_recommendation": "Maintenance recipe",
      "daily_tasks": ["Task 1", "Task 2"]
    }}
  ],
  "stage_composts": [
    {{
      "stage_name": "1. Basal / Land Preparation & Sowing",
      "days_range": "Days 0 - 15",
      "compost_type": "{fertilizer_type}",
      "recommended_compost": "Exact formulation",
      "dosage": "e.g. 8-10 tons / acre or 50 kg / acre",
      "application_method": "Exact incorporation or side dress method",
      "water_tips": "Moisture advice"
    }},
    {{
      "stage_name": "2. Vegetative Growth Stage",
      "days_range": "Days 16 - 35",
      "compost_type": "{fertilizer_type}",
      "recommended_compost": "Exact formulation",
      "dosage": "e.g. 500 kg / acre",
      "application_method": "Application method",
      "water_tips": "Moisture advice"
    }},
    {{
      "stage_name": "3. Flowering Stage",
      "days_range": "Days 36 - 55",
      "compost_type": "{fertilizer_type}",
      "recommended_compost": "Exact formulation",
      "dosage": "Dosage",
      "application_method": "Application method",
      "water_tips": "Moisture advice"
    }},
    {{
      "stage_name": "4. Fruit / Pod Development",
      "days_range": "Days 56 - 80",
      "compost_type": "{fertilizer_type}",
      "recommended_compost": "Exact formulation",
      "dosage": "Dosage",
      "application_method": "Application method",
      "water_tips": "Moisture advice"
    }},
    {{
      "stage_name": "5. Harvesting & Maturity",
      "days_range": "Days 81 - 105",
      "compost_type": "{fertilizer_type}",
      "recommended_compost": "Exact formulation",
      "dosage": "Dosage",
      "application_method": "Application method",
      "water_tips": "Moisture advice"
    }}
  ]
}}
"""

        try:
            raw_response = GeminiService.generate_content(
                prompt=prompt,
                temperature=0.3,
                timeout=20
            )

            # Strip any markdown code fences if present
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            
            parsed_plan = json.loads(cleaned)
            if parsed_plan and "growth_stages" in parsed_plan and "stage_composts" in parsed_plan:
                logger.info(f"Successfully generated dynamic agronomic plan via Gemini for {clean_crop}")
                return parsed_plan
        except Exception as gemini_err:
            logger.warning(f"Gemini dynamic plan generation notice: {gemini_err}. Falling back to curated agronomic knowledge.")

        # Step 3: Verified Agronomic Knowledge Fallback
        preset = None
        for k in AGRONOMIC_KNOWLEDGE_PRESETS:
            if k in clean_key:
                preset = AGRONOMIC_KNOWLEDGE_PRESETS[k]
                break

        if not preset:
            preset = AGRONOMIC_KNOWLEDGE_PRESETS["tomato"]

        return {
            "crop_name": clean_crop,
            "variety": variety,
            "total_days": preset["total_days"],
            "planting_method": planting_method,
            "fertilizer_type": fertilizer_type,
            "recommended_season": season,
            "water_requirements": preset["water_requirements"],
            "irrigation_method": preset["irrigation_method"],
            "fertilizer_guidance": preset["fertilizer_guidance"],
            "common_problems": preset["common_problems"],
            "basic_solutions": preset["basic_solutions"],
            "growth_stages": preset["stages"],
            "stage_composts": preset["composts"]
        }
