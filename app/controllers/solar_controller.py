from flask import request

from app.models.solar_guide import SolarGuide
from app.utils.decorators import success_response, error_response


def get_guides():
    """
    Get all solar farming guides. Supports optional ?category= filter and pagination.
    ---
    tags: [Solar Farming Guidance]
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    category = request.args.get("category")

    query = SolarGuide.query
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(SolarGuide.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        {
            "items": [g.to_dict(include_content=False) for g in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    )


def get_guide_detail(guide_id):
    """
    Get full details of a single solar farming guide.
    ---
    tags: [Solar Farming Guidance]
    """
    guide = SolarGuide.query.get(guide_id)
    if not guide:
        return error_response("Guide not found", 404)
    return success_response(guide.to_dict(include_content=True))
