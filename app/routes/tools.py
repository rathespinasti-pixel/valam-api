from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.tool_listing import ToolListing
from app.utils.decorators import success_response, error_response, get_current_user

tools_bp = Blueprint("tools", __name__, url_prefix="/api/tools")


@tools_bp.route("", methods=["GET"])
def get_tools():
    """Get available equipment/tools for lending in Vavuniya."""
    category = request.args.get("category")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = ToolListing.query.filter_by(is_available=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            (ToolListing.tool_name.ilike(f"%{search}%")) | (ToolListing.description.ilike(f"%{search}%"))
        )

    pagination = query.order_by(ToolListing.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response({
        "items": [tool.to_dict() for tool in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


@tools_bp.route("/<int:tool_id>", methods=["GET"])
def get_tool_detail(tool_id):
    """Get detail of a tool listing."""
    tool = ToolListing.query.get(tool_id)
    if not tool:
        return error_response("Tool listing not found", 404)
    return success_response(tool.to_dict())


@tools_bp.route("", methods=["POST"])
@jwt_required()
def create_tool_listing():
    """List a tool/equipment for lending."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    tool_name = data.get("tool_name")
    rental_price_per_day = data.get("rental_price_per_day")
    contact_phone = data.get("contact_phone") or user.phone

    if not tool_name or rental_price_per_day is None or not contact_phone:
        return error_response("tool_name, rental_price_per_day and contact_phone are required", 400)

    tool = ToolListing(
        owner_id=user.id,
        tool_name=tool_name,
        description=data.get("description"),
        category=data.get("category", "Equipment"),
        rental_price_per_day=rental_price_per_day,
        location=data.get("location", user.farm_location or "Vavuniya"),
        contact_phone=contact_phone,
        image_url=data.get("image_url"),
    )
    db.session.add(tool)
    db.session.commit()

    return success_response(tool.to_dict(), message="Tool listing created successfully", status_code=201)


@tools_bp.route("/<int:tool_id>", methods=["PUT"])
@jwt_required()
def update_tool_listing(tool_id):
    """Update a tool listing. Only owner or admin may update."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    tool = ToolListing.query.get(tool_id)
    if not tool:
        return error_response("Tool listing not found", 404)

    if tool.owner_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    for field in (
        "tool_name", "description", "category", "rental_price_per_day",
        "location", "contact_phone", "is_available", "image_url"
    ):
        if field in data:
            setattr(tool, field, data[field])

    db.session.commit()
    return success_response(tool.to_dict(), message="Tool listing updated successfully")


@tools_bp.route("/<int:tool_id>", methods=["DELETE"])
@jwt_required()
def delete_tool_listing(tool_id):
    """Delete a tool listing. Only owner or admin may delete."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    tool = ToolListing.query.get(tool_id)
    if not tool:
        return error_response("Tool listing not found", 404)

    if tool.owner_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    db.session.delete(tool)
    db.session.commit()
    return success_response(message="Tool listing deleted successfully")
