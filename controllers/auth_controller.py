from flask import Blueprint, g, jsonify, request, send_from_directory
from sqlalchemy import select

from config import Config
from database.session import SessionLocal
from models.user import User
from services.auth_service import (
    authenticate_user,
    change_user_password,
    create_password_reset_code,
    register_user,
    reset_password_with_code,
    update_user_profile,
)
from services.email_service import EmailConfigurationError, send_password_reset_code
from services.file_service import save_image
from utils.auth import jwt_required
from utils.jwt import create_access_token


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    registration_code = (data.get("registration_code") or "").strip()

    if not username or not email or not password or not registration_code:
        return jsonify({"error": "username_email_password_code_required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password_min_8_chars"}), 400
    if registration_code != Config.REGISTRATION_CODE:
        return jsonify({"error": "invalid_registration_code"}), 403

    db = SessionLocal()
    try:
        user = register_user(db, username=username, email=email, password=password)
        token = create_access_token(user.id)
        return jsonify({"user": user.to_dict(), "access_token": token}), 201
    except ValueError as exc:
        db.rollback()
        return jsonify({"error": str(exc)}), 409
    finally:
        db.close()


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email_password_required"}), 400

    db = SessionLocal()
    try:
        user = authenticate_user(db, email=email, password=password)
        if not user:
            return jsonify({"error": "invalid_credentials"}), 401
        token = create_access_token(user.id)
        return jsonify({"user": user.to_dict(), "access_token": token})
    finally:
        db.close()


@auth_bp.post("/auth/password/forgot")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()

    if not email:
        return jsonify({"error": "email_required"}), 400

    db = SessionLocal()
    try:
        reset_code = create_password_reset_code(db, email=email)
        if reset_code:
            try:
                send_password_reset_code(email, reset_code)
            except EmailConfigurationError as exc:
                return jsonify({"error": str(exc)}), 503
            except Exception:
                return jsonify({"error": "password_reset_email_failed"}), 502
        return jsonify({"message": "password_reset_code_sent"})
    finally:
        db.close()


@auth_bp.post("/auth/password/reset")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""

    if not email or not code or not new_password:
        return jsonify({"error": "email_code_new_password_required"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "password_min_8_chars"}), 400

    db = SessionLocal()
    try:
        if not reset_password_with_code(db, email, code, new_password):
            return jsonify({"error": "invalid_or_expired_reset_code"}), 400
        return jsonify({"message": "password_reset_success"})
    finally:
        db.close()


@auth_bp.put("/auth/me/password")
@jwt_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "current_password_new_password_required"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "password_min_8_chars"}), 400

    if not change_user_password(g.db, g.current_user, current_password, new_password):
        return jsonify({"error": "invalid_current_password"}), 401
    return jsonify({"message": "password_changed"})


@auth_bp.get("/auth/me")
@jwt_required
def me():
    return jsonify({"user": g.current_user.to_dict()})


@auth_bp.get("/users/<int:user_id>")
def get_user_profile(user_id: int):
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            return jsonify({"error": "user_not_found"}), 404
        return jsonify({"user": user.to_public_dict()})
    finally:
        db.close()


@auth_bp.get("/users/by-username/<username>")
def get_user_profile_by_username(username: str):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username))
        if not user:
            return jsonify({"error": "user_not_found"}), 404
        return jsonify({"user": user.to_public_dict()})
    finally:
        db.close()


@auth_bp.put("/auth/me/profile")
@jwt_required
def update_profile():
    data = request.form if request.form else request.get_json(silent=True) or {}

    try:
        profile_photo_url = save_image(
            request.files.get("profile_photo"),
            Config.UPLOAD_DIRECTORIES["profile_photos"],
        )
        banner_photo_url = save_image(
            request.files.get("banner_photo"),
            Config.UPLOAD_DIRECTORIES["banners"],
        )
        user = update_user_profile(
            g.db,
            g.current_user,
            username=(data.get("username") or "").strip() or None,
            bio=data.get("bio"),
            profile_photo_url=profile_photo_url,
            banner_photo_url=banner_photo_url,
        )
        return jsonify({"user": user.to_dict()})
    except ValueError as exc:
        g.db.rollback()
        status_code = 400 if str(exc) == "invalid_image_type" else 409
        return jsonify({"error": str(exc)}), status_code


@auth_bp.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)
