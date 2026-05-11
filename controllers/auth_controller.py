from flask import Blueprint, g, jsonify, request, send_from_directory

from config import Config
from database.session import SessionLocal
from services.auth_service import authenticate_user, register_user, update_user_profile
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

    if not username or not email or not password:
        return jsonify({"error": "username_email_password_required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password_min_8_chars"}), 400

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


@auth_bp.get("/auth/me")
@jwt_required
def me():
    return jsonify({"user": g.current_user.to_dict()})


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
