from flask import Blueprint, g, jsonify, request

from database.session import SessionLocal
from models.comment import Comment
from models.post import Post
from services.file_service import save_post_media
from services.post_service import (
    create_comment,
    create_post,
    get_post,
    like_comment,
    like_post,
    list_posts,
    unlike_comment,
    unlike_post,
)
from config import Config
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
        "author": serialize_author(comment.author),
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "likes_count": len(comment.likes),
        "liked_by": [serialize_author(like.user) for like in comment.likes],
        "replies": [serialize_comment(reply) for reply in comment.replies],
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    }


def serialize_media(media) -> dict:
    return {
        "id": media.id,
        "url": media.url,
        "media_type": media.media_type,
        "filename": media.filename,
        "position": media.position,
    }


def serialize_post(post: Post) -> dict:
    root_comments = [comment for comment in post.comments if comment.parent_id is None]
    return {
        "id": post.id,
        "content": post.content,
        "author": serialize_author(post.author),
        "media": [serialize_media(media) for media in post.media],
        "likes_count": len(post.likes),
        "liked_by": [serialize_author(like.user) for like in post.likes],
        "comments": [serialize_comment(comment) for comment in root_comments],
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@post_bp.post("/posts")
@jwt_required
def publish_post():
    data = request.form if request.form else request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    files = request.files.getlist("media")

    try:
        media_files = save_post_media(files, Config.UPLOAD_DIRECTORIES["posts"])
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not content and not media_files:
        return jsonify({"error": "content_or_media_required"}), 400

    post = create_post(g.db, g.current_user, content, media_files)
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
    parent_id = data.get("parent_id")

    if not content:
        return jsonify({"error": "content_required"}), 400
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_parent_id"}), 400

    try:
        comment = create_comment(g.db, g.current_user, post_id, content, parent_id)
        db = SessionLocal()
        try:
            reloaded_post = get_post(db, post_id)
            reloaded_comment = next(
                item for item in reloaded_post.comments if item.id == comment.id
            )
            return jsonify({"comment": serialize_comment(reloaded_comment)}), 201
        finally:
            db.close()
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404


@post_bp.post("/posts/<int:post_id>/likes")
@jwt_required
def like_one_post(post_id: int):
    try:
        like_post(g.db, g.current_user, post_id)
        post = get_post(g.db, post_id)
        return jsonify({"post": serialize_post(post)})
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404


@post_bp.delete("/posts/<int:post_id>/likes")
@jwt_required
def unlike_one_post(post_id: int):
    try:
        unlike_post(g.db, g.current_user, post_id)
        post = get_post(g.db, post_id)
        return jsonify({"post": serialize_post(post)})
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404


@post_bp.post("/comments/<int:comment_id>/likes")
@jwt_required
def like_one_comment(comment_id: int):
    try:
        like_comment(g.db, g.current_user, comment_id)
        return jsonify({"message": "comment_liked"})
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404


@post_bp.delete("/comments/<int:comment_id>/likes")
@jwt_required
def unlike_one_comment(comment_id: int):
    try:
        unlike_comment(g.db, g.current_user, comment_id)
        return jsonify({"message": "comment_unliked"})
    except ValueError as exc:
        g.db.rollback()
        return jsonify({"error": str(exc)}), 404
