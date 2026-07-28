from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.crop import Crop
from app.utils.decorators import success_response, error_response, get_current_user

crops_bp = Blueprint("crops", __name__, url_prefix="/api/crops")


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
        area_size=data.get("area_size"),
        current_stage=data.get("current_stage", "Vegetative stage"),
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
    for field in ("crop_name", "variety", "area_size", "current_stage", "notes", "is_active"):
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
