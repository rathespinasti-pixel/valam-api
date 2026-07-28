from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.community import CommunityPost, Comment
from app.utils.decorators import success_response, error_response, get_current_user

community_bp = Blueprint("community", __name__, url_prefix="/api/community")


@community_bp.route("/posts", methods=["GET"])
def get_posts():
    """Get community discussion posts with optional ?category= and ?search= filtering."""
    category = request.args.get("category")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = CommunityPost.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            (CommunityPost.title.ilike(f"%{search}%")) | (CommunityPost.content.ilike(f"%{search}%"))
        )

    pagination = query.order_by(CommunityPost.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response({
        "items": [post.to_dict(include_comments=False) for post in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
    })


@community_bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post_detail(post_id):
    """Get detailed community post along with comments."""
    post = CommunityPost.query.get(post_id)
    if not post:
        return error_response("Post not found", 404)
    return success_response(post.to_dict(include_comments=True))


@community_bp.route("/posts", methods=["POST"])
@jwt_required()
def create_post():
    """Create a new community discussion post."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return error_response("title and content are required", 400)

    post = CommunityPost(
        user_id=user.id,
        title=title,
        content=content,
        category=data.get("category", "General"),
        image_url=data.get("image_url"),
    )
    db.session.add(post)
    db.session.commit()

    return success_response(post.to_dict(include_comments=True), message="Post created successfully", status_code=201)


@community_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(post_id):
    """Add a comment to a community post."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    post = CommunityPost.query.get(post_id)
    if not post:
        return error_response("Post not found", 404)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return error_response("content is required", 400)

    comment = Comment(post_id=post.id, user_id=user.id, content=content)
    db.session.add(comment)
    db.session.commit()

    return success_response(comment.to_dict(), message="Comment added successfully", status_code=201)


@community_bp.route("/posts/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    """Delete a post. Only post owner or admin may delete."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    post = CommunityPost.query.get(post_id)
    if not post:
        return error_response("Post not found", 404)

    if post.user_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    db.session.delete(post)
    db.session.commit()
    return success_response(message="Post deleted successfully")
