from flask import request

from app.extensions import db
from app.models.chat import ChatHistory
from app.utils.decorators import success_response, error_response, get_current_user
from app.utils.ai_client import ask_ai_assistant

QUESTION_CROP_ALIASES = [
    ("maize", ("maize", "corn")),
    ("tomato", ("tomato",)),
    ("chilli", ("chilli", "chili")),
    ("pumpkin", ("pumpkin",)),
]


def _find_question_crop_alias(question):
    q = (question or "").lower()
    for _, aliases in QUESTION_CROP_ALIASES:
        if any(alias in q for alias in aliases):
            return aliases
    return None


def _crop_matches_aliases(crop, aliases):
    crop_name = (crop.get("crop_name") or "").lower()
    return any(alias in crop_name for alias in aliases)


def ask():
    """
    Ask the AI farming assistant a question with full user & crop context awareness.
    ---
    tags: [Chatbot]
    """
    from datetime import date, datetime
    from app.models.crop import Crop

    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    category = (data.get("category") or "").strip() or None
    language = (data.get("language") or getattr(user, "preferred_language", "en") or "en").strip()
    page_context = data.get("page_context") or {}

    if not question:
        return error_response("question is required", 400)

    # 1. Fetch all active crops for this user from database
    user_crops = Crop.query.filter_by(user_id=user.id, is_active=True).all()
    focused_crop_id = page_context.get("focused_crop_id")
    question_crop_aliases = _find_question_crop_alias(question)
    crops_context = []
    today = date.today()
    for c in user_crops:
        days_old = None
        if c.planting_date:
            try:
                p_date = c.planting_date
                if isinstance(p_date, str):
                    p_date = datetime.strptime(p_date[:10], "%Y-%m-%d").date()
                elif isinstance(p_date, datetime):
                    p_date = p_date.date()
                if isinstance(p_date, date):
                    days_old = (today - p_date).days
            except Exception:
                pass
        crops_context.append({
            "id": c.id,
            "crop_name": c.crop_name,
            "variety": c.variety or "Standard",
            "planting_date": str(c.planting_date),
            "days_after_planting": days_old,
            "current_stage": c.current_stage or "Active Growth",
            "planting_method": getattr(c, "planting_method", "Direct Seeding"),
            "irrigation_type": getattr(c, "irrigation_type", "Drip Irrigation"),
            "fertilizer_preference": getattr(c, "fertilizer_preference", "Organic"),
            "land_size": getattr(c, "land_size", None),
            "land_size_unit": getattr(c, "land_size_unit", "Acres"),
            "notes": getattr(c, "notes", None)
        })

    focused_crop = None
    if question_crop_aliases:
        focused_crop = next((crop for crop in crops_context if _crop_matches_aliases(crop, question_crop_aliases)), None)

    if focused_crop is None and focused_crop_id:
        try:
            focused_crop_id = int(focused_crop_id)
            focused_crop = next((crop for crop in crops_context if crop.get("id") == focused_crop_id), None)
        except (TypeError, ValueError):
            pass

    if focused_crop:
        focused_crop["is_focused"] = True
        crops_context = [focused_crop]
        if isinstance(page_context, dict):
            page_context = dict(page_context)
            page_context.pop("active_crops", None)
            page_context["focused_crop"] = {
                **focused_crop,
                **(page_context.get("focused_crop") or {}),
                "crop_name": focused_crop.get("crop_name"),
            }
            page_context["exclusive_crop_context"] = True

    # 2. Extract Farmer Profile Metadata
    user_profile = {
        "full_name": user.full_name,
        "district": getattr(user, "district", "Vavuniya") or "Vavuniya",
        "ds_division": getattr(user, "ds_division", "Vavuniya Town") or "Vavuniya Town",
        "farming_category": getattr(user, "farming_category", "Farmer") or "Farmer",
        "land_size": getattr(user, "land_size", 1.0) or 1.0,
        "land_size_unit": getattr(user, "land_size_unit", "Acres") or "Acres",
        "irrigation_preference": getattr(user, "irrigation_preference", "Drip Irrigation") or "Drip Irrigation",
        "fertilizer_preference": getattr(user, "fertilizer_preference", "Organic") or "Organic",
        "preferred_language": language
    }

    full_context = {
        "profile": user_profile,
        "crops": crops_context,
        "page_context": page_context
    }

    answer = ask_ai_assistant(question, category, language, user_context=full_context)

    entry = ChatHistory(user_id=user.id, question=question, answer=answer)
    db.session.add(entry)
    db.session.commit()

    return success_response({
        **entry.to_dict(),
        "context_applied": {
            "active_crops_count": len(crops_context),
            "crops": [f"{c['crop_name']} ({c['current_stage']}, Day {c['days_after_planting']})" for c in crops_context]
        }
    }, message="Answer generated successfully")


def history():
    """
    View chat history for the logged-in user.
    ---
    tags: [Chatbot]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = ChatHistory.query.filter_by(user_id=user.id).order_by(ChatHistory.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(
        {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    )


def delete_history(history_id):
    """
    Delete a chat history entry.
    ---
    tags: [Chatbot]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    entry = ChatHistory.query.get(history_id)
    if not entry:
        return error_response("History entry not found", 404)

    if entry.user_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    db.session.delete(entry)
    db.session.commit()
    return success_response(message="History entry deleted successfully")
