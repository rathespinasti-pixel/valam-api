import json
import logging
import requests
from flask import current_app
from app.extensions import db
from app.models.perenual_plant import PerenualPlant

logger = logging.getLogger(__name__)

# Fallback reference data when API key is rate-limited, unconfigured, or plant search is empty
FALLBACK_BOTANICAL_DATA = {
    "tomato": {
        "scientific_name": "Solanum lycopersicum",
        "family": "Solanaceae (Nightshade)",
        "plant_type": "Annual Vegetable Vine",
        "growth_habit": "Indeterminate / Bush Vine",
        "sunlight_requirement": "Full Sun (6-8 hours daily)",
        "water_requirement": "Frequent (3.5 - 4.5 L/m² daily)",
        "maintenance_level": "Medium (Staking & Pruning required)",
        "soil_preference": "Well-drained, fertile sandy loam (pH 6.0 - 6.8)",
        "hardiness": "Zones 10 - 12",
        "description": "Tomato is a nightshade family crop cultivated worldwide for its edible fleshy red fruits rich in Lycopene, Vitamin C, and Potassium.",
        "image_url": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=600&q=80"
        ]
    },
    "chili": {
        "scientific_name": "Capsicum annuum",
        "family": "Solanaceae (Nightshade)",
        "plant_type": "Perennial / Annual Bush",
        "growth_habit": "Compact Branching Bush",
        "sunlight_requirement": "Full Sun",
        "water_requirement": "Moderate (2.0 - 3.0 L/m² daily)",
        "maintenance_level": "Low - Medium",
        "soil_preference": "Well-drained loamy soil",
        "hardiness": "Zones 9 - 11",
        "description": "Chili pepper plants produce pungent fruit pods containing capsaicin, widely grown across tropical regions.",
        "image_url": "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=600&q=80"
        ]
    },
    "eggplant": {
        "scientific_name": "Solanum melongena",
        "family": "Solanaceae (Nightshade)",
        "plant_type": "Warm-season Perennial Bush",
        "growth_habit": "Erect Woody Shrub",
        "sunlight_requirement": "Full Sun",
        "water_requirement": "High (3.0 - 4.5 L/m² daily)",
        "maintenance_level": "Medium",
        "soil_preference": "Rich organic loam with good drainage",
        "hardiness": "Zones 9 - 12",
        "description": "Eggplant (Brinjal) is a species of nightshade grown for its glossy purple fleshy fruit.",
        "image_url": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80"
        ]
    },
    "okra": {
        "scientific_name": "Abelmoschus esculentus",
        "family": "Malvaceae (Mallow)",
        "plant_type": "Warm-season Annual",
        "growth_habit": "Tall Upright Stalk",
        "sunlight_requirement": "Full Sun",
        "water_requirement": "Moderate (2.5 - 3.5 L/m² daily)",
        "maintenance_level": "Low",
        "soil_preference": "Sandy loam to clay loam",
        "hardiness": "Zones 8 - 11",
        "description": "Okra is a flowering plant valued for its edible green seed pods.",
        "image_url": "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1599818804921-2e65005db379?auto=format&fit=crop&w=600&q=80"
        ]
    },
    "red onion": {
        "scientific_name": "Allium cepa",
        "family": "Amaryllidaceae",
        "plant_type": "Biennial Bulb Crop",
        "growth_habit": "Tubular Foliage & Bulb",
        "sunlight_requirement": "Full Sun",
        "water_requirement": "Light & Frequent",
        "maintenance_level": "Medium (Weeding & Earthing up)",
        "soil_preference": "Well-drained sandy loam",
        "hardiness": "Zones 4 - 10",
        "description": "Red onions are cultivars of the onion with purplish-red skin and white flesh tinged with red.",
        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"
        ]
    },
    "paddy": {
        "scientific_name": "Oryza sativa",
        "family": "Poaceae (Grass)",
        "plant_type": "Annual Cereal Grass",
        "growth_habit": "Erect Tiller Clump",
        "sunlight_requirement": "Full Sun",
        "water_requirement": "High / Standing Water (2-5cm)",
        "maintenance_level": "Medium",
        "soil_preference": "Puddled heavy clay loam",
        "hardiness": "Zones 9 - 12",
        "description": "Paddy rice is the agricultural crop harvested for rice grain staple consumption worldwide.",
        "image_url": "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80",
        "reference_images": [
            "https://images.unsplash.com/photo-1530507629858-e4977d30e9e0?auto=format&fit=crop&w=600&q=80"
        ]
    }
}


class PerenualService:
    @staticmethod
    def get_plant_info(crop_name: str) -> dict:
        if not crop_name:
            crop_name = "Tomato"

        clean_name = crop_name.strip()
        search_key = clean_name.lower()

        # 1. Check local database cache first
        try:
            cached = PerenualPlant.query.filter(PerenualPlant.crop_name.ilike(clean_name)).first()
            if cached:
                logger.info(f"Retrieved Perenual plant info from DB cache for: {clean_name}")
                return cached.to_dict()
        except Exception as e:
            logger.warning(f"DB cache check error: {e}")

        # 2. Prepare API call configuration
        api_key = current_app.config.get("PERENUAL_API_KEY", "")
        base_url = current_app.config.get("PERENUAL_BASE_URL", "https://perenual.com/api")

        plant_dict = None

        if api_key and api_key != "YOUR_API_KEY":
            try:
                # Perenual Species Search API
                search_url = f"{base_url}/species-list"
                params = {"key": api_key, "q": clean_name}
                logger.info(f"Querying Perenual API for species: {clean_name}")
                
                resp = requests.get(search_url, params=params, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    data_items = data.get("data", [])
                    if isinstance(data_items, list) and len(data_items) > 0:
                        first_item = data_items[0]
                        species_id = first_item.get("id")

                        # Call Details API for deep information if species_id exists
                        details_url = f"{base_url}/species/details/{species_id}"
                        detail_resp = requests.get(details_url, params={"key": api_key}, timeout=6)
                        detail_data = detail_resp.json() if detail_resp.status_code == 200 else first_item

                        # Helper to format array fields into friendly string
                        def format_list(val):
                            if isinstance(val, list):
                                return ", ".join([str(v) for v in val if v])
                            return str(val) if val else None

                        sci_names = detail_data.get("scientific_name")
                        sci_str = format_list(sci_names) if sci_names else None

                        sunlight_val = format_list(detail_data.get("sunlight"))
                        soil_val = format_list(detail_data.get("soil"))

                        # Reference images resolution
                        default_img_obj = detail_data.get("default_image") or {}
                        main_img = default_img_obj.get("regular_url") or default_img_obj.get("original_url") or default_img_obj.get("thumbnail")
                        
                        ref_imgs = []
                        if main_img:
                            ref_imgs.append(main_img)

                        plant_dict = {
                            "crop_name": clean_name,
                            "perenual_id": species_id,
                            "scientific_name": sci_str or detail_data.get("common_name", clean_name),
                            "family": detail_data.get("family") or "Solanaceae",
                            "plant_type": detail_data.get("type") or "Vegetable / Crop",
                            "growth_habit": detail_data.get("growth_habit") or "Upright Cultivation",
                            "sunlight_requirement": sunlight_val or "Full sun",
                            "water_requirement": detail_data.get("watering") or "Average",
                            "maintenance_level": detail_data.get("maintenance") or "Medium",
                            "soil_preference": soil_val or "Well-drained fertile soil",
                            "hardiness": f"Zones {detail_data.get('hardiness', {}).get('min', '4')} - {detail_data.get('hardiness', {}).get('max', '11')}" if isinstance(detail_data.get("hardiness"), dict) else "Tropical & Subtropical",
                            "description": detail_data.get("description") or f"{clean_name} is a high-yielding crop cultivated widely in agricultural divisions.",
                            "image_url": main_img,
                            "reference_images": ref_imgs,
                            "raw_json": json.dumps(detail_data),
                        }
                else:
                    logger.warning(f"Perenual API HTTP {resp.status_code}: {resp.text}")
            except Exception as req_err:
                logger.error(f"Perenual API request exception: {req_err}")

        # 3. If API yielded no result or failed, use clean fallback data for known crops
        if not plant_dict:
            fb = None
            for k in FALLBACK_BOTANICAL_DATA:
                if k in search_key:
                    fb = FALLBACK_BOTANICAL_DATA[k]
                    break
            if not fb:
                fb = FALLBACK_BOTANICAL_DATA["tomato"]

            plant_dict = {
                "crop_name": clean_name,
                "perenual_id": None,
                "scientific_name": fb["scientific_name"],
                "family": fb["family"],
                "plant_type": fb["plant_type"],
                "growth_habit": fb["growth_habit"],
                "sunlight_requirement": fb["sunlight_requirement"],
                "water_requirement": fb["water_requirement"],
                "maintenance_level": fb["maintenance_level"],
                "soil_preference": fb["soil_preference"],
                "hardiness": fb["hardiness"],
                "description": fb["description"],
                "image_url": fb["image_url"],
                "reference_images": fb["reference_images"],
                "raw_json": None,
            }

        # 4. Save to Database Cache
        try:
            record = PerenualPlant(
                crop_name=clean_name,
                perenual_id=plant_dict.get("perenual_id"),
                scientific_name=plant_dict.get("scientific_name"),
                family=plant_dict.get("family"),
                plant_type=plant_dict.get("plant_type"),
                growth_habit=plant_dict.get("growth_habit"),
                sunlight_requirement=plant_dict.get("sunlight_requirement"),
                water_requirement=plant_dict.get("water_requirement"),
                maintenance_level=plant_dict.get("maintenance_level"),
                soil_preference=plant_dict.get("soil_preference"),
                hardiness=plant_dict.get("hardiness"),
                description=plant_dict.get("description"),
                image_url=plant_dict.get("image_url"),
                raw_json=plant_dict.get("raw_json"),
            )
            record.set_reference_images(plant_dict.get("reference_images", []))
            db.session.add(record)
            db.session.commit()
            logger.info(f"Cached Perenual plant info in database for: {clean_name}")
            return record.to_dict()
        except Exception as save_err:
            db.session.rollback()
            logger.error(f"Error saving Perenual cache to DB: {save_err}")
            return plant_dict
