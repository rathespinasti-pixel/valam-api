import base64
import hashlib
import json
import time

import requests
from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.managed_crop import (ManagedCrop, CropLifecycleStage, PlantingMethod,
    SoilRequirement, Compost, Fertilizer, Irrigation, Pest, CropDisease, HarvestInformation)
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.utils.decorators import error_response, get_current_user, success_response

managed_crops_bp = Blueprint("managed_crops", __name__)
public_catalogue_bp = Blueprint("public_crop_catalogue", __name__)

SECTIONS = {
    "lifecycle_stages": (CropLifecycleStage, True), "planting_methods": (PlantingMethod, True),
    "soil_requirements": (SoilRequirement, True), "composts": (Compost, True),
    "fertilizers": (Fertilizer, True), "irrigations": (Irrigation, True),
    "pests": (Pest, True), "diseases": (CropDisease, True),
    "harvest_information": (HarvestInformation, False),
}


def admin_user():
    user = get_current_user()
    return user if user and user.role in ("admin", "super_admin") else None


def clean_fields(model, data):
    allowed = {c.name for c in model.__table__.columns} - {"id", "crop_id", "created_at", "updated_at"}
    return {key: value for key, value in (data or {}).items() if key in allowed}


def replace_sections(crop, data):
    for key, (model, many) in SECTIONS.items():
        if key not in data:
            continue
        old = getattr(crop, key)
        if many:
            for row in list(old):
                db.session.delete(row)
            for item in data.get(key) or []:
                db.session.add(model(crop_id=crop.id, **clean_fields(model, item)))
        else:
            if old:
                db.session.delete(old)
            item = data.get(key)
            if item:
                db.session.add(model(crop_id=crop.id, **clean_fields(model, item)))


def apply_basic(crop, data, user_id):
    mapping = ("name", "scientific_name", "category", "description", "suitable_regions", "suitable_seasons")
    for field in mapping:
        if field in data:
            setattr(crop, field, data[field].strip() if isinstance(data[field], str) else data[field])
    crop.updated_by = user_id


@managed_crops_bp.route("", methods=["GET"])
@jwt_required()
def list_admin_crops():
    if not admin_user(): return error_response("Admin authorization required", 403)
    crops = ManagedCrop.query.order_by(ManagedCrop.updated_at.desc()).all()
    return success_response({"items": [c.to_dict(False) for c in crops], "total": len(crops)})


@managed_crops_bp.route("", methods=["POST"])
@jwt_required()
def create_crop():
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    data = request.get_json(silent=True) or {}
    if not str(data.get("name", "")).strip(): return error_response("Crop name is required", 400)
    crop = ManagedCrop(name=data["name"].strip(), created_by=user.id, updated_by=user.id, status="draft")
    apply_basic(crop, data, user.id)
    try:
        db.session.add(crop); db.session.flush(); replace_sections(crop, data); db.session.commit()
    except IntegrityError:
        db.session.rollback(); return error_response("A crop with this name already exists", 409)
    return success_response(crop.to_dict(), "Crop saved as draft", 201)


@managed_crops_bp.route("/<int:crop_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def crop_detail(crop_id):
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    crop = ManagedCrop.query.get(crop_id)
    if not crop: return error_response("Crop not found", 404)
    if request.method == "GET": return success_response(crop.to_dict())
    if request.method == "DELETE":
        crop.status = "inactive"; crop.updated_by = user.id; db.session.commit()
        return success_response(crop.to_dict(False), "Crop deactivated")
    data = request.get_json(silent=True) or {}; apply_basic(crop, data, user.id); replace_sections(crop, data)
    try: db.session.commit()
    except IntegrityError: db.session.rollback(); return error_response("A crop with this name already exists", 409)
    return success_response(crop.to_dict(), "Crop changes saved")


@managed_crops_bp.route("/<int:crop_id>/lifecycle", methods=["POST"])
@jwt_required()
def add_lifecycle_stage(crop_id):
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    crop = ManagedCrop.query.get(crop_id)
    if not crop: return error_response("Crop not found", 404)
    data = request.get_json(silent=True) or {}
    if not str(data.get("stage_name", "")).strip(): return error_response("Stage name is required", 400)
    if "stage_order" not in data: data["stage_order"] = len(crop.lifecycle_stages) + 1
    stage = CropLifecycleStage(crop_id=crop.id, **clean_fields(CropLifecycleStage, data))
    crop.updated_by = user.id; db.session.add(stage); db.session.commit()
    return success_response(stage.to_dict(), "Lifecycle stage added", 201)


@managed_crops_bp.route("/<int:crop_id>/lifecycle/<int:stage_id>", methods=["PUT", "DELETE"])
@jwt_required()
def edit_lifecycle_stage(crop_id, stage_id):
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    stage = CropLifecycleStage.query.filter_by(id=stage_id, crop_id=crop_id).first()
    if not stage: return error_response("Lifecycle stage not found", 404)
    if request.method == "DELETE":
        db.session.delete(stage); message = "Lifecycle stage deleted"
    else:
        for field, value in clean_fields(CropLifecycleStage, request.get_json(silent=True) or {}).items(): setattr(stage, field, value)
        message = "Lifecycle stage updated"
    crop = ManagedCrop.query.get(crop_id); crop.updated_by = user.id; db.session.commit()
    return success_response(None if request.method == "DELETE" else stage.to_dict(), message)


@managed_crops_bp.route("/<int:crop_id>/<action>", methods=["POST"])
@jwt_required()
def change_status(crop_id, action):
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    if action not in ("publish", "activate", "deactivate"): return error_response("Invalid action", 404)
    crop = ManagedCrop.query.get(crop_id)
    if not crop: return error_response("Crop not found", 404)
    if action == "publish" and (not crop.name or not crop.lifecycle_stages):
        return error_response("A crop name and at least one lifecycle stage are required before publishing", 400)
    crop.status = "published" if action in ("publish", "activate") else "inactive"
    crop.updated_by = user.id; db.session.commit()
    return success_response(crop.to_dict(), f"Crop {crop.status}")


@managed_crops_bp.route("/<int:crop_id>/ai-suggestions", methods=["POST"])
@jwt_required()
def ai_suggestions(crop_id):
    if not admin_user(): return error_response("Admin authorization required", 403)
    crop = ManagedCrop.query.get(crop_id)
    if not crop: return error_response("Crop not found", 404)
    prompt = f'''Suggest an agronomically cautious crop profile for {crop.name} ({crop.scientific_name or 'scientific name unknown'}).
Return ONLY valid JSON with keys: description, suitable_regions, suitable_seasons, lifecycle_stages,
planting_methods, soil_requirements, composts, fertilizers, irrigations, pests, diseases, harvest_information.
Lifecycle stages are an array with stage_name, stage_order, start_day, end_day, duration, description, recommended_activities.
Other arrays should use the field names expected by an agricultural management system. Do not use markdown.
These are suggestions for admin review, never final prescriptions or published content.'''
    try:
        raw = GeminiService.generate_content(prompt, temperature=0.35, timeout=30)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        suggestions = json.loads(raw)
    except (GeminiServiceError, json.JSONDecodeError) as exc:
        return error_response(f"AI suggestions are unavailable: {str(exc)}", 502)
    return success_response({"suggestions": suggestions, "review_required": True}, "AI suggestions ready for admin review")


@managed_crops_bp.route("/<int:crop_id>/lifecycle/<int:stage_id>/generate-image", methods=["POST"])
@jwt_required()
def generate_stage_image(crop_id, stage_id):
    if not admin_user(): return error_response("Admin authorization required", 403)
    crop = ManagedCrop.query.get(crop_id); stage = CropLifecycleStage.query.filter_by(id=stage_id, crop_id=crop_id).first()
    if not crop or not stage: return error_response("Crop or lifecycle stage not found", 404)
    prompt = f"A realistic agricultural photograph of {crop.name} during the {stage.stage_name} lifecycle stage. {stage.description or ''} Accurate plant morphology, natural farm lighting, no text or labels."
    try: image_bytes, mime = GeminiService.generate_image(prompt)
    except GeminiServiceError as exc: return error_response(f"Image generation failed: {str(exc)}", 502)
    preview = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    return success_response({"preview": preview, "prompt": prompt, "approved": False}, "Preview generated; approval required")


@managed_crops_bp.route("/<int:crop_id>/lifecycle/<int:stage_id>/approve-image", methods=["POST"])
@jwt_required()
def approve_stage_image(crop_id, stage_id):
    user = admin_user()
    if not user: return error_response("Admin authorization required", 403)
    stage = CropLifecycleStage.query.filter_by(id=stage_id, crop_id=crop_id).first()
    if not stage: return error_response("Lifecycle stage not found", 404)
    preview = (request.get_json(silent=True) or {}).get("preview", "")
    if not preview.startswith("data:image/"): return error_response("A generated image preview is required", 400)
    cloud, api_key, secret = (current_app.config.get(x, "") for x in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"))
    if not all((cloud, api_key, secret)): return error_response("Cloudinary storage is not configured", 503)
    timestamp = int(time.time()); folder = "valam/crop-lifecycle"
    signature = hashlib.sha1(f"folder={folder}&timestamp={timestamp}{secret}".encode()).hexdigest()
    try:
        response = requests.post(f"https://api.cloudinary.com/v1_1/{cloud}/image/upload",
            data={"file": preview, "api_key": api_key, "timestamp": timestamp, "folder": folder, "signature": signature}, timeout=45)
        response.raise_for_status(); image_url = response.json()["secure_url"]
    except (requests.RequestException, KeyError): return error_response("Cloudinary image upload failed", 502)
    stage.image_url = image_url; stage.image_source = "gemini"; stage.image_approved = True
    crop = ManagedCrop.query.get(crop_id); crop.updated_by = user.id; db.session.commit()
    return success_response(stage.to_dict(), "Image approved and stored")


@public_catalogue_bp.route("", methods=["GET"])
def public_crops():
    crops = ManagedCrop.query.filter_by(status="published").order_by(ManagedCrop.name).all()
    return success_response({"items": [c.to_dict(False) for c in crops], "total": len(crops)})


@public_catalogue_bp.route("/<int:crop_id>", methods=["GET"])
def public_crop(crop_id):
    crop = ManagedCrop.query.filter_by(id=crop_id, status="published").first()
    return success_response(crop.to_dict()) if crop else error_response("Published crop not found", 404)
