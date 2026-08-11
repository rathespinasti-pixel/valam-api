from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.crop_guide import CropGuide
from app.utils.decorators import success_response, error_response, get_current_user

crop_guides_bp = Blueprint("crop_guides", __name__)


@crop_guides_bp.route("", methods=["GET"])
def get_crop_guides():
    """Get crop calendar and guides. Supports ?crop_name= and ?season= filtering."""
    crop_name = request.args.get("crop_name")
    season = request.args.get("season")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = CropGuide.query
    if crop_name:
        query = query.filter(CropGuide.crop_name.ilike(f"%{crop_name}%"))
    if season:
        query = query.filter(CropGuide.recommended_season.ilike(f"%{season}%"))

    pagination = query.order_by(CropGuide.crop_name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response({
        "items": [guide.to_dict() for guide in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


@crop_guides_bp.route("/<int:guide_id>", methods=["GET"])
def get_crop_guide_detail(guide_id):
    """Get single crop guide details."""
    guide = CropGuide.query.get(guide_id)
    if not guide:
        return error_response("Crop guide not found", 404)
    return success_response(guide.to_dict())


@crop_guides_bp.route("", methods=["POST"])
@jwt_required()
def create_crop_guide():
    """Admin endpoint to create a crop guide."""
    user = get_current_user()
    if not user or user.role not in ["admin", "super_admin"]:
        return error_response("Admin privileges required", 403)

    data = request.get_json(silent=True) or {}
    crop_name = data.get("crop_name")
    if not crop_name:
        return error_response("crop_name is required", 400)

    guide = CropGuide(
        crop_name=crop_name,
        variety=data.get("variety"),
        recommended_season=data.get("recommended_season", "Yala"),
        planting_method=data.get("planting_method", "Direct Seeding"),
        fertilizer_type=data.get("fertilizer_type", "Organic"),
        water_requirements=data.get("water_requirements"),
        fertilizer_guidance=data.get("fertilizer_guidance"),
        common_problems=data.get("common_problems"),
        basic_solutions=data.get("basic_solutions"),
        image_url=data.get("image_url"),
    )

    stages = data.get("growth_stages")
    if isinstance(stages, list):
        guide.set_growth_stages(stages)

    composts = data.get("stage_composts")
    if isinstance(composts, list):
        guide.set_stage_composts(composts)

    db.session.add(guide)
    db.session.commit()

    return success_response(guide.to_dict(), message="Crop guide created successfully", status_code=201)


@crop_guides_bp.route("/<int:guide_id>", methods=["PUT"])
@jwt_required()
def update_crop_guide(guide_id):
    """Admin endpoint to update a crop guide."""
    user = get_current_user()
    if not user or user.role not in ["admin", "super_admin"]:
        return error_response("Admin privileges required", 403)

    guide = CropGuide.query.get(guide_id)
    if not guide:
        return error_response("Crop guide not found", 404)

    data = request.get_json(silent=True) or {}
    fields = (
        "crop_name", "variety", "recommended_season", "planting_method",
        "fertilizer_type", "water_requirements", "fertilizer_guidance",
        "common_problems", "basic_solutions", "image_url"
    )
    for field in fields:
        if field in data:
            setattr(guide, field, data[field])

    if "growth_stages" in data and isinstance(data["growth_stages"], list):
        guide.set_growth_stages(data["growth_stages"])

    if "stage_composts" in data and isinstance(data["stage_composts"], list):
        guide.set_stage_composts(data["stage_composts"])

    db.session.commit()
    return success_response(guide.to_dict(), message="Crop guide updated successfully")


@crop_guides_bp.route("/<int:guide_id>", methods=["DELETE"])
@jwt_required()
def delete_crop_guide(guide_id):
    """Admin endpoint to delete a crop guide."""
    user = get_current_user()
    if not user or user.role not in ["admin", "super_admin"]:
        return error_response("Admin privileges required", 403)

    guide = CropGuide.query.get(guide_id)
    if not guide:
        return error_response("Crop guide not found", 404)

    db.session.delete(guide)
    db.session.commit()
    return success_response(message="Crop guide deleted successfully")


@crop_guides_bp.route("/suggest-agronomy", methods=["POST"])
@jwt_required()
def suggest_agronomy():
    """
    Admin AI & Agricultural API suggestion engine to auto-generate
    scientific crop lifecycles, water requirements, and 5-stage compost schedules.
    """
    user = get_current_user()
    if not user or user.role not in ["admin", "super_admin"]:
        return error_response("Admin privileges required", 403)

    data = request.get_json(silent=True) or {}
    crop_name = data.get("crop_name", "Tomato").strip()
    variety = data.get("variety", "Standard").strip()
    planting_method = data.get("planting_method", "Direct Seeding").strip()
    fertilizer_type = data.get("fertilizer_type", "Organic").strip()
    season = data.get("season", "Yala & Maha").strip()
    district = data.get("district", "Vavuniya").strip()

    from app.services.agronomy_engine_service import AgronomyEngineService
    plan = AgronomyEngineService.suggest_crop_plan(
        crop_name=crop_name,
        variety=variety,
        planting_method=planting_method,
        fertilizer_type=fertilizer_type,
        season=season,
        district=district
    )

    return success_response(plan, message=f"Agronomic plan suggested for {crop_name}")


