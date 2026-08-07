import base64
import logging
import os
import re
import uuid
from datetime import datetime

from flask import current_app, request

from app.extensions import db
from app.models.crop_lifecycle_image import CropLifecycleImage
from app.services.gemini_service import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)

GENERATED_IMAGE_URL_PREFIX = "/static/generated/lifecycle"

# Curated stock photography used ONLY as a fallback when live Gemini image
# generation cannot be reached (missing/invalid key, quota exhausted, network
# failure). Every crop below maps to its OWN imagery - there is intentionally
# NO catch-all branch anywhere in this module that substitutes a different
# crop's (e.g. tomato's) photos for a crop that isn't recognised here. Crops
# that aren't in this map fall through to a generated placeholder instead
# (see `_placeholder_data_uri`) so an unrecognised crop never gets mislabeled
# as tomato.
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
    """Service for generating and caching crop-specific lifecycle imagery.

    Flow per get_or_generate_lifecycle_image() call:
      1. Look up a cached image in the DB (crop_name + stage) -> return it.
      2. Otherwise call Gemini's IMAGE model to generate a fresh photo.
      3. If Gemini generation fails or is unavailable (no key, quota
         exhausted, network error), fall back to curated stock imagery for
         that specific crop, or a generated placeholder if the crop has no
         curated entry. It never substitutes another crop's photo.
      4. Persist whichever image_url was produced and return it.
    """

    @classmethod
    def get_stage_key(cls, stage_name: str) -> str:
        s = (stage_name or "").lower().strip()
        if "seedling" in s or "nursery" in s or "stage 1" in s or "நாற்று" in s or "தவா" in s or "පැළ" in s:
            return "seedling"
        if "vegetative" in s or "growth" in s or "stage 2" in s or "வளர்ச்சி" in s or "වර්ධන" in s:
            return "vegetative"
        if "flower" in s or "bloom" in s or "stage 3" in s or "பூக்கும்" in s or "மல்" in s:
            return "flowering"
        if "fruit" in s or "matur" in s or "pod" in s or "stage 4" in s or "காய்" in s or "ඵල" in s:
            return "fruiting"
        if "harvest" in s or "pick" in s or "stage 5" in s or "அறுவடை" in s or "අස්වැන්න" in s:
            return "harvest"
        if "1" in s: return "seedling"
        if "2" in s: return "vegetative"
        if "3" in s: return "flowering"
        if "4" in s: return "fruiting"
        if "5" in s: return "harvest"
        return "vegetative"

    @classmethod
    def get_crop_key(cls, crop_name: str):
        """Return the matching key in CROP_SPECIFIC_VISUAL_MAPS, or None.

        Deliberately returns None instead of defaulting to "tomato" - a crop
        the app doesn't recognise must never silently be presented as a
        tomato.
        """
        c = (crop_name or "").lower().strip()
        for key in CROP_SPECIFIC_VISUAL_MAPS:
            if key in c:
                return key
        return None

    @staticmethod
    def _placeholder_data_uri(crop_name: str, stage_key: str) -> str:
        """Self-contained, crop-labelled placeholder for crops with no
        curated stock photo and no live Gemini image available.

        This is a small inline SVG (no external request, so it can never
        404 or hotlink-break), with a colour deterministically derived from
        the crop name so different crops are visibly distinct from one
        another even before a real photo/AI image exists for them.
        """
        import hashlib
        seed = hashlib.md5(f"{(crop_name or '').lower()}::{stage_key}".encode("utf-8")).hexdigest()
        hue = int(seed[:3], 16) % 360
        bg = f"hsl({hue},45%,88%)"
        fg = f"hsl({hue},55%,30%)"
        crop_label = (crop_name or "Crop").strip().title()
        stage_label = (stage_key or "growth").replace("_", " ").title()

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
            f'<rect width="100%" height="100%" fill="{bg}"/>'
            f'<text x="50%" y="45%" font-family="Segoe UI, Arial, sans-serif" font-size="42" '
            f'font-weight="700" fill="{fg}" text-anchor="middle">{crop_label}</text>'
            f'<text x="50%" y="58%" font-family="Segoe UI, Arial, sans-serif" font-size="24" '
            f'fill="{fg}" text-anchor="middle">{stage_label} stage</text>'
            f'<text x="50%" y="68%" font-family="Segoe UI, Arial, sans-serif" font-size="14" '
            f'fill="{fg}" text-anchor="middle" opacity="0.75">Photo not yet available</text>'
            f'</svg>'
        )
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    @classmethod
    def get_crop_specific_visual(cls, crop_name: str, stage_name: str) -> str:
        stage_key = cls.get_stage_key(stage_name)
        crop_key = cls.get_crop_key(crop_name)
        if crop_key is None:
            return cls._placeholder_data_uri(crop_name, stage_key)
        crop_map = CROP_SPECIFIC_VISUAL_MAPS[crop_key]
        return crop_map.get(stage_key, crop_map.get("default"))

    @staticmethod
    def _build_prompt(crop_name: str, stage_name: str, crop_age: int) -> str:
        return (
            f"A realistic, photorealistic agricultural photograph of a healthy {crop_name} plant, "
            f"approximately {crop_age} days after planting, currently in its {stage_name} growth "
            f"stage. Show accurate {crop_name} leaf shape, plant structure and coloration typical of "
            f"this exact growth stage. Natural outdoor farm field setting, daylight, sharp focus, "
            f"no text, no watermark, no illustration/cartoon style."
        )

    @staticmethod
    def _save_generated_image(image_bytes: bytes, mime_type: str, crop_name: str, stage_key: str) -> str:
        """Persist raw image bytes under app/static/generated/lifecycle and
        return an absolute URL to it."""
        ext = "png"
        if "jpeg" in mime_type or "jpg" in mime_type:
            ext = "jpg"
        elif "webp" in mime_type:
            ext = "webp"

        static_folder = current_app.static_folder if current_app else None
        if not static_folder:
            raise GeminiServiceError("Flask static folder is not configured; cannot persist generated image.")

        safe_crop = re.sub(r"[^a-z0-9]+", "-", (crop_name or "crop").lower()).strip("-") or "crop"
        filename = f"{safe_crop}_{stage_key}_{uuid.uuid4().hex[:10]}.{ext}"

        target_dir = os.path.join(static_folder, "generated", "lifecycle")
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, filename), "wb") as f:
            f.write(image_bytes)

        relative_url = f"{GENERATED_IMAGE_URL_PREFIX}/{filename}"
        try:
            return request.host_url.rstrip("/") + relative_url
        except RuntimeError:
            # Called outside of a request context (e.g. a script/test) - fall
            # back to a relative URL; the frontend already prefixes API paths
            # with its configured backend base URL.
            return relative_url

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

        # 2. Attempt live Gemini image generation
        prompt = cls._build_prompt(clean_crop, clean_stage, crop_age)
        image_url = None
        source = "gemini_generated"
        try:
            image_bytes, mime_type = GeminiService.generate_image(prompt)
            image_url = cls._save_generated_image(image_bytes, mime_type, clean_crop, stage_key)
            logger.info(f"Generated new Gemini AI image for {clean_crop} - {stage_key}")
        except GeminiServiceError as err:
            logger.warning(f"Gemini image generation unavailable for {clean_crop} ({stage_key}): {err}")
        except Exception as err:
            logger.error(f"Unexpected error generating Gemini image for {clean_crop} ({stage_key}): {err}")

        if not image_url:
            image_url = cls.get_crop_specific_visual(clean_crop, clean_stage)
            source = "fallback_stock" if cls.get_crop_key(clean_crop) else "fallback_placeholder"
            logger.warning(
                f"Falling back to {source} imagery for {clean_crop} ({stage_key}) - "
                f"live Gemini generation was unavailable."
            )

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
            logger.info(f"Saved new lifecycle image to DB for {clean_crop} - {stage_key} (source={source})")
            result = new_record.to_dict()
            result["source"] = source
            return result
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
                "generated_date": datetime.utcnow().isoformat(),
                "source": source,
            }
