from flask import Blueprint, g, jsonify, request

from database.session import SessionLocal
from models.comment import Comment
from models.post import Post
from services.post_service import create_comment, create_post, get_post, list_posts
from utils.auth import jwt_required


post_bp = Blueprint("posts", __name__)


def serialize_author(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "profile_photo_url": user.profile_photo_url,
    }


def serialize_comment(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "author_id": comment.author_id,
        "post_id": comment.post_id,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    }


def serialize_post(post: Post) -> dict:
    return {
        "id": post.id,
        "content": post.content,
        "author": serialize_author(post.author),
        "comments": [serialize_comment(comment) for comment in post.comments],
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@post_bp.post("/posts")
@jwt_required
def publish_post():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "content_required"}), 400

    post = create_post(g.db, g.current_user, content)
    db = SessionLocal()
    try:
        reloaded_post = get_post(db, post.id)
        return jsonify({"post": serialize_post(reloaded_post)}), 201
    finally:
        db.close()


@post_bp.get("/posts")
def get_posts():
    db = SessionLocal()
    try:
        return jsonify({"posts": [serialize_post(post) for post in list_posts(db)]})
    finally:
        db.close()


@post_bp.get("/posts/<int:post_id>")
def get_one_post(post_id: int):
    db = SessionLocal()
    try:
        post = get_post(db, post_id)
        if not post:
            return jsonify({"error": "post_not_found"}), 404
        return jsonify({"post": serialize_post(post)})
    finally:
        db.close()


@post_bp.post("/posts/<int:post_id>/comments")
@jwt_required
def comment_post(post_id: int):
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "content_required"}), 400

    try:
        comment = create_comment(g.db, g.current_user, post_id, content)
        return jsonify({"comment": serialize_comment(comment)}), 201
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404
