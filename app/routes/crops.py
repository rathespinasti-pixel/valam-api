from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.crop import Crop
from app.utils.decorators import success_response, error_response, get_current_user

crops_bp = Blueprint("crops", __name__)


@crops_bp.route("", methods=["GET"])
@jwt_required()
def get_crops():
    """Get active crops for the logged-in farmer."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    query = Crop.query.filter_by(user_id=user.id, is_active=True).order_by(Crop.planting_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        "items": [crop.to_dict() for crop in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


@crops_bp.route("", methods=["POST"])
@jwt_required()
def add_crop():
    """Add a new crop to cultivation tracking."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    crop_name = data.get("crop_name")
    planting_date_str = data.get("planting_date")

    if not crop_name or not planting_date_str:
        return error_response("crop_name and planting_date are required", 400)

    try:
        planting_date = datetime.strptime(planting_date_str, "%Y-%m-%d").date()
    except ValueError:
        return error_response("planting_date must be in YYYY-MM-DD format", 400)

    crop = Crop(
        user_id=user.id,
        crop_name=crop_name.strip(),
        variety=data.get("variety"),
        planting_date=planting_date,
        planting_method=data.get("planting_method", "Transplanting"),
        land_size=data.get("land_size") or (user.land_size if user.land_size else 0.5),
        land_size_unit=data.get("land_size_unit") or (user.land_size_unit if user.land_size_unit else "Acres"),
        irrigation_type=data.get("irrigation_type") or (user.irrigation_preference if user.irrigation_preference else "Drip Irrigation"),
        fertilizer_preference=data.get("fertilizer_preference") or (user.fertilizer_preference if user.fertilizer_preference else "Organic"),
        area_size=data.get("area_size") or f"{data.get('land_size', 0.5)} {data.get('land_size_unit', 'Acres')}",
        current_stage=data.get("current_stage", "Stage 1: Seedling / Nursery / Transplanting"),
        notes=data.get("notes"),
    )
    db.session.add(crop)
    db.session.commit()

    return success_response(crop.to_dict(), message="Crop added successfully", status_code=201)


@crops_bp.route("/<int:crop_id>", methods=["PUT"])
@jwt_required()
def update_crop(crop_id):
    """Update growth stage or details of a crop."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    crop = Crop.query.get(crop_id)
    if not crop or crop.user_id != user.id:
        return error_response("Crop not found or forbidden", 404)

    data = request.get_json(silent=True) or {}
    fields = (
        "crop_name", "variety", "area_size", "current_stage", "notes", "is_active",
        "planting_method", "land_size", "land_size_unit", "irrigation_type", "fertilizer_preference"
    )
    for field in fields:
        if field in data:
            setattr(crop, field, data[field])

    if "planting_date" in data and data["planting_date"]:
        try:
            crop.planting_date = datetime.strptime(data["planting_date"], "%Y-%m-%d").date()
        except ValueError:
            return error_response("planting_date must be in YYYY-MM-DD format", 400)

    db.session.commit()
    return success_response(crop.to_dict(), message="Crop updated successfully")


@crops_bp.route("/<int:crop_id>", methods=["DELETE"])
@jwt_required()
def delete_crop(crop_id):
    """Remove a crop record."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    crop = Crop.query.get(crop_id)
    if not crop or crop.user_id != user.id:
        return error_response("Crop not found or forbidden", 404)

    crop.is_active = False
    db.session.commit()
    return success_response(message="Crop removed successfully")


@crops_bp.route("/plant-info", methods=["GET"])
def get_plant_info():
    """Retrieve Perenual botanical plant info (cached in local DB)."""
    crop_name = request.args.get("crop_name") or request.args.get("q") or "Tomato"
    from app.services.perenual_service import PerenualService
    plant_info = PerenualService.get_plant_info(crop_name)
    return success_response(plant_info)


@crops_bp.route("/lifecycle-image", methods=["POST"])
@jwt_required()
def get_lifecycle_image():
    """
    POST /api/crops/lifecycle-image
    Fetch or generate dynamic crop lifecycle image using Gemini AI with variety & stage isolation.
    """
    data = request.get_json(silent=True) or {}
    crop_name = data.get("crop_name")
    stage = data.get("stage")
    variety = data.get("variety")
    crop_id = data.get("crop_id")
    crop_age = data.get("crop_age", 30)
    variety = data.get("variety")
    planting_method = data.get("planting_method")

    # Verify user authentication
    current_user = get_current_user()
    if not current_user:
        return error_response("User authentication required", 403)

    # Optional: ensure the crop belongs to the user if crop_id is provided
    if crop_id:
        from app.models.crop import Crop
        crop_obj = Crop.query.get(crop_id)
        if not crop_obj or crop_obj.user_id != current_user.id:
            return error_response("Crop not found or access denied", 404)

    if not crop_name or not stage:
        return error_response("crop_name and stage are required parameters.", 400)

    from app.services.gemini_image_service import GeminiImageService
    result = GeminiImageService.get_or_generate_lifecycle_image(
        crop_name=crop_name,
        stage=stage,
        variety=variety,
        crop_id=crop_id,
        crop_age=crop_age,
        variety=variety,
        planting_method=planting_method,
    )
    return success_response(result)


