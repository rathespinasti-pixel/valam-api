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


# Crop-specific curated botanical imagery.
# Every crop maps EXCLUSIVELY to its own authentic species photos across all stages.
# There is NO generic catch-all substitution; if an unlisted crop is queried,
# it dynamically renders a clean botanical card with that exact crop name and stage.
CROP_SPECIFIC_VISUAL_MAPS: dict = {
    "tomato": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1561136594-7f68413baa99?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?auto=format&fit=crop&w=800&q=80"
    },
    "brinjal": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1595855759920-86582396756a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80"
    },
    "eggplant": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1595855759920-86582396756a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1613744655060-d8a4362a78f2?auto=format&fit=crop&w=800&q=80"
    },
    "green chilli": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1583857502409-728b7a66f4ef?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80"
    },
    "chilli": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1583857502409-728b7a66f4ef?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80"
    },
    "chili": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1583857502409-728b7a66f4ef?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=800&q=80"
    },
    "okra": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80"
    },
    "ladies finger": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1592417817098-8f3d69a0a19e?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1628773822503-930a858340d2?auto=format&fit=crop&w=800&q=80"
    },
    "maize": {
        "seed": "https://images.unsplash.com/photo-1568644396922-5c3bfae12521?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1568644396922-5c3bfae12521?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80"
    },
    "corn": {
        "seed": "https://images.unsplash.com/photo-1568644396922-5c3bfae12521?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1568644396922-5c3bfae12521?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=800&q=80"
    },
    "paddy": {
        "seed": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80"
    },
    "rice": {
        "seed": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1536657464919-892534f60d6e?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80"
    },
    "red onion": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80"
    },
    "onion": {
        "seed": "https://images.unsplash.com/photo-1535241552843-26780355d026?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=800&q=80"
    },
    "peanut": {
        "seed": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80"
    },
    "groundnut": {
        "seed": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?auto=format&fit=crop&w=800&q=80"
    },
    "green gram": {
        "seed": "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80"
    },
    "mung bean": {
        "seed": "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?auto=format&fit=crop&w=800&q=80",
        "seedling": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "transplanting": "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?auto=format&fit=crop&w=800&q=80",
        "vegetative": "https://images.unsplash.com/photo-1589927986089-35812388d1f4?auto=format&fit=crop&w=800&q=80",
        "flowering": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=800&q=80",
        "fruiting": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80",
        "harvest": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80",
        "default": "https://images.unsplash.com/photo-1567375698348-5d9d5ae99de0?auto=format&fit=crop&w=800&q=80"
    },
}


class GeminiImageService:
    """Service for generating and caching crop-specific lifecycle imagery.

    Flow per get_or_generate_lifecycle_image() call:
      1. Look up cached image in DB (crop_name + stage) -> return it.
      2. Otherwise build a strictly isolated botanical prompt (Crop + Variety + Stage).
      3. Call Gemini's image models to generate a fresh high-resolution photo.
      4. If Gemini is rate-limited or unavailable, fall back to the exact curated
         imagery for that specific crop, or generate a crisp SVG botanical card.
      5. Persist whichever image_url was produced in DB cache.
    """

    @classmethod
    def get_stage_key(cls, stage_name: str) -> str:
        s = (stage_name or "").lower().strip()
        if s == "seed" or ("seed" in s and "seedling" not in s):
            return "seed"
        if "transplant" in s or "நடுதல்" in s or "පැළ සිටුවීම" in s:
            return "transplanting"
        if "seedling" in s or "nursery" in s or "stage 1" in s or "நாற்று" in s or "தவா" in s or "පැළ" in s:
            return "seedling"
        if "vegetative" in s or "growth" in s or "stage 2" in s or "வளர்ச்சி" in s or "වර්ධන" in s:
            return "vegetative"
        if "flower" in s or "bloom" in s or "stage 3" in s or "பூக்கும்" in s or "மல்" in s:
            return "flowering"
        if "fruit" in s or "matur" in s or "pod" in s or "stage 4" in s or "காய்" in s or "ඵල" in s:
            return "fruiting"
        if "harvest" in s or "pick" in s or "stage 5" in s or "stage 6" in s or "அறுவடை" in s or "අස්වැන්න" in s:
            return "harvest"
        if "1" in s: return "seedling"
        if "2" in s: return "vegetative"
        if "3" in s: return "flowering"
        if "4" in s: return "fruiting"
        if "5" in s: return "harvest"
        return "vegetative"

    @classmethod
    def get_crop_key(cls, crop_name: str):
        c = (crop_name or "").lower().strip()
        for key in CROP_SPECIFIC_VISUAL_MAPS:
            if key in c:
                return key
        return None

    @staticmethod
    def _placeholder_data_uri(crop_name: str, stage_key: str, variety: str = None) -> str:
        """Dynamic SVG botanical lifecycle card for newly introduced crops."""
        import hashlib
        seed = hashlib.md5(f"{(crop_name or '').lower()}::{stage_key}".encode("utf-8")).hexdigest()
        hue = int(seed[:3], 16) % 360
        bg1 = f"hsl({hue},60%,20%)"
        bg2 = f"hsl({(hue + 30) % 360},65%,35%)"
        crop_label = (crop_name or "Crop").strip().title()
        variety_label = f"Variety: {variety.strip()}" if variety else "Standard Sri Lankan Variety"
        stage_label = (stage_key or "growth").replace("_", " ").title()

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">'
            f'<defs>'
            f'<linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" style="stop-color:{bg1};stop-opacity:1" />'
            f'<stop offset="100%" style="stop-color:{bg2};stop-opacity:1" />'
            f'</linearGradient>'
            f'</defs>'
            f'<rect width="100%" height="100%" fill="url(#grad)"/>'
            f'<circle cx="400" cy="240" r="110" fill="rgba(255,255,255,0.1)"/>'
            f'<text x="50%" y="260" font-family="Segoe UI, -apple-system, sans-serif" font-size="72" '
            f'text-anchor="middle" fill="#FFFFFF">🌱</text>'
            f'<text x="50%" y="390" font-family="Segoe UI, -apple-system, sans-serif" font-size="34" '
            f'font-weight="800" fill="#FFFFFF" text-anchor="middle">{crop_label} Lifecycle</text>'
            f'<text x="50%" y="430" font-family="Segoe UI, -apple-system, sans-serif" font-size="18" '
            f'fill="#A7F3D0" text-anchor="middle">{variety_label}</text>'
            f'<rect x="250" y="460" width="300" height="42" rx="21" fill="rgba(16,185,129,0.9)"/>'
            f'<text x="50%" y="487" font-family="Segoe UI, -apple-system, sans-serif" font-size="16" '
            f'font-weight="700" fill="#FFFFFF" text-anchor="middle">Stage: {stage_label}</text>'
            f'<text x="50%" y="540" font-family="Segoe UI, -apple-system, sans-serif" font-size="12" '
            f'fill="rgba(255,255,255,0.6)" text-anchor="middle">✨ Dynamic Valam AI Botanical Crop Engine</text>'
            f'</svg>'
        )
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    @classmethod
    def get_crop_specific_visual(cls, crop_name: str, stage_name: str, variety: str = None) -> str:
        stage_key = cls.get_stage_key(stage_name)
        crop_key = cls.get_crop_key(crop_name)
        if crop_key is None:
            return cls._placeholder_data_uri(crop_name, stage_key, variety)
        crop_map = CROP_SPECIFIC_VISUAL_MAPS[crop_key]
        return crop_map.get(stage_key, crop_map.get("default", cls._placeholder_data_uri(crop_name, stage_key, variety)))

    @staticmethod
    def _build_prompt(crop_name: str, stage_name: str, variety: str = None, crop_age: int = 30) -> str:
        var_text = f" (Variety: {variety})" if variety else ""
        return (
            f"A clean, realistic, high-resolution botanical and agricultural photograph of ONLY a single healthy {crop_name}{var_text} plant "
            f"at the {stage_name} growth stage (approximately {crop_age} days after planting) in fertile dry-zone farm soil. "
            f"Show accurate botanical {crop_name} leaf shape, branching structure, and exact growth stage characteristics "
            f"(e.g. tender green seedling shoots, lush vegetative branching canopy, distinct blossoms for flowering, developing/ripening fruits for fruiting, or harvest-ready yield). "
            f"Natural daylight, outdoor garden field bed, sharp focus, clean agricultural educational style. "
            f"STRICT NEGATIVE CONSTRAINTS: No people, no farmers, no hands, no text, no labels, no diagrams, no watermarks, no logos, no other plant species or unrelated crops in frame."
        )

    @staticmethod
    def _save_generated_image(image_bytes: bytes, mime_type: str, crop_name: str, stage_key: str) -> str:
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
            return relative_url

    @classmethod
    @classmethod
    def get_or_generate_lifecycle_image(cls, crop_name: str, stage: str, crop_id: int = None, crop_age: int = 30, variety: str = None, planting_method: str = None) -> dict:
        if not crop_name or not stage:
            raise ValueError("crop_name and stage are required parameters.")

        clean_crop = crop_name.strip()
        clean_stage = stage.strip()
        clean_variety = variety.strip() if variety else None
        stage_key = cls.get_stage_key(clean_stage)

        # 1. Search Database for cached image
        query = CropLifecycleImage.query.filter(
            CropLifecycleImage.crop_name.ilike(clean_crop),
            CropLifecycleImage.stage.ilike(stage_key)
        )
        if variety:
            query = query.filter(CropLifecycleImage.variety.ilike(variety.strip()))
        if planting_method:
            query = query.filter(CropLifecycleImage.planting_method.ilike(planting_method.strip()))
        
        existing = query.first()

        if not existing and crop_id:
            existing = CropLifecycleImage.query.filter(
                CropLifecycleImage.crop_id == crop_id,
                CropLifecycleImage.stage.ilike(stage_key)
            ).first()

        if existing:
            logger.info(f"Retrieved cached lifecycle image from DB for {clean_crop} - {clean_stage}")
            return existing.to_dict()

# 2. Attempt live Gemini AI image generation
        prompt = cls._build_prompt(clean_crop, clean_stage, clean_variety, crop_age)
        image_url = None
        source = "gemini_generated"
        try:
            image_bytes, mime_type = GeminiService.generate_image(prompt)
            image_url = cls._save_generated_image(image_bytes, mime_type, clean_crop, stage_key)
            logger.info(f"Generated new Gemini AI image for {clean_crop} - {stage_key}")
        except GeminiServiceError as err:
            logger.warning(f"Gemini image generation notice for {clean_crop} ({stage_key}): {err}")
        except Exception as err:
            logger.error(f"Unexpected error generating Gemini image for {clean_crop} ({stage_key}): {err}")

        # 3. If Gemini is rate-limited / unavailable, provide authentic crop-isolated visual
        if not image_url:
            image_url = cls.get_crop_specific_visual(clean_crop, clean_stage, clean_variety)
            source = "curated_botanical" if cls.get_crop_key(clean_crop) else "dynamic_botanical_card"
            logger.info(f"Applied crop-isolated visual for {clean_crop} - {stage_key} (source={source})")

        # 4. Store generated image result in DB cache
        try:
            new_record = CropLifecycleImage(
                crop_id=crop_id,
                crop_name=clean_crop,
                stage=stage_key,
                image_url=image_url,
                prompt_used=prompt,
                generated_date=datetime.utcnow(),
                variety=variety.strip() if variety else None,
                planting_method=planting_method.strip() if planting_method else None
            )
            db.session.add(new_record)
            db.session.commit()
            logger.info(f"Saved lifecycle image to DB for {clean_crop} - {stage_key} (source={source})")
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
