from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.chat import ChatHistory
from app.utils.decorators import success_response, error_response, get_current_user
from app.utils.ai_client import ask_ai_assistant

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask():
    """
    Ask the AI farming assistant a question.
    ---
    tags: [Chatbot]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    category = (data.get("category") or "").strip() or None
    language = (data.get("language") or getattr(user, "preferred_language", "en") or "en").strip()

    if not question:
        return error_response("question is required", 400)

    answer = ask_ai_assistant(question, category, language)

    entry = ChatHistory(user_id=user.id, question=question, answer=answer)
    db.session.add(entry)
    db.session.commit()

    return success_response(entry.to_dict(), message="Answer generated successfully")


@chatbot_bp.route("/history", methods=["GET"])
@jwt_required()
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


@chatbot_bp.route("/history/<int:history_id>", methods=["DELETE"])
@jwt_required()
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
