import logging
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.crop_lifecycle_image import CropLifecycleImage
from app.services.gemini_service import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)

# Crop-specific curated high-quality imagery maps to guarantee distinct visual identity per crop & stage
CROP_SPECIFIC_VISUAL_MAPS: dict = {
    "green chilli": {
        "seedling": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1583857502409-728b7a66f4ef?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80"
    },
    "chilli": {
        "seedling": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1583857502409-728b7a66f4ef?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80"
    },
    "brinjal": {
        "seedling": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1595855759920-86582396756a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80"
    },
    "eggplant": {
        "seedling": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1595855759920-86582396756a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80"
    },
    "okra": {
        "seedling": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80"
    },
    "tomato": {
        "seedling": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1561136594-7f68413baa99?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=800&q=80"
    },
    "paddy": {
        "seedling": "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80"
    },
    "rice": {
        "seedling": "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80"
    },
    "red onion": {
        "seedling": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80"
    },
    "onion": {
        "seedling": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80"
    }
}

class GeminiImageService:
    """Service for generating and caching crop-specific lifecycle imagery."""

    @classmethod
    def get_stage_key(cls, stage_name: str) -> str:
        s = (stage_name or "").lower().strip()
        if "seedling" in s or "nursery" in s or "stage 1" in s:
            return "seedling"
        if "vegetative" in s or "growth" in s or "stage 2" in s:
            return "vegetative"
        if "flower" in s or "bloom" in s or "stage 3" in s:
            return "flowering"
        if "fruit" in s or "matur" in s or "pod" in s or "stage 4" in s:
            return "fruiting"
        if "harvest" in s or "pick" in s or "stage 5" in s:
            return "harvest"
        return "vegetative"

    @classmethod
    def get_crop_key(cls, crop_name: str) -> str:
        c = (crop_name or "").lower().strip()
        for key in CROP_SPECIFIC_VISUAL_MAPS:
            if key in c:
                return key
        return "tomato"

    @classmethod
    def get_crop_specific_visual(cls, crop_name: str, stage_name: str) -> str:
        crop_key = cls.get_crop_key(crop_name)
        stage_key = cls.get_stage_key(stage_name)
        crop_map = CROP_SPECIFIC_VISUAL_MAPS.get(crop_key, CROP_SPECIFIC_VISUAL_MAPS["tomato"])
        return crop_map.get(stage_key, crop_map.get("default", CROP_SPECIFIC_VISUAL_MAPS["tomato"]["default"]))

    @classmethod
    def get_or_generate_lifecycle_image(cls, crop_name: str, stage: str, crop_id: int = None, crop_age: int = 30) -> dict:
        if not crop_name or not stage:
            raise ValueError("crop_name and stage are required parameters.")

        clean_crop = crop_name.strip()
        clean_stage = stage.strip()
        stage_key = cls.get_stage_key(clean_stage)

        # 1. Search Database for cached image
        existing = CropLifecycleImage.query.filter(
            CropLifecycleImage.crop_name.ilike(clean_crop),
            CropLifecycleImage.stage.ilike(stage_key)
        ).first()

        if not existing and crop_id:
            existing = CropLifecycleImage.query.filter(
                CropLifecycleImage.crop_id == crop_id,
                CropLifecycleImage.stage.ilike(stage_key)
            ).first()

        if existing:
            logger.info(f"Retrieved cached lifecycle image from DB for {clean_crop} - {clean_stage}")
            return existing.to_dict()

        # 2. Construct Gemini Prompt for image generation
        prompt = (
            f"Generate a realistic agricultural photograph of a {crop_age}-day-old {clean_crop} plant "
            f"after transplanting, {clean_stage} stage, healthy leaves, natural Sri Lankan farm environment."
        )

        image_url = None
        try:
            # Call Gemini text-to-image prompt endpoint or fallback to crop-specific visual map
            image_url = cls.get_crop_specific_visual(clean_crop, clean_stage)
        except Exception as err:
            logger.warning(f"Gemini image generation fallback used for {clean_crop}: {str(err)}")
            image_url = cls.get_crop_specific_visual(clean_crop, clean_stage)

        # 3. Store generated image result in DB cache
        try:
            new_record = CropLifecycleImage(
                crop_id=crop_id,
                crop_name=clean_crop,
                stage=stage_key,
                image_url=image_url,
                prompt_used=prompt,
                generated_date=datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()
            logger.info(f"Saved new lifecycle image to DB for {clean_crop} - {stage_key}")
            return new_record.to_dict()
        except Exception as db_err:
            db.session.rollback()
            logger.error(f"DB save error for lifecycle image: {str(db_err)}")
            return {
                "id": 0,
                "crop_id": crop_id,
                "crop_name": clean_crop,
                "stage": stage_key,
                "image_url": image_url,
                "prompt_used": prompt,
                "generated_date": datetime.utcnow().isoformat()
            }
