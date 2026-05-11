from functools import wraps

import jwt
from flask import g, jsonify, request
from sqlalchemy import select

from database.session import SessionLocal
from models.user import User
from utils.jwt import decode_access_token


def jwt_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")

        if scheme.lower() != "bearer" or not token:
            return jsonify({"error": "missing_bearer_token"}), 401

        try:
            payload = decode_access_token(token)
            user_id = int(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return jsonify({"error": "invalid_token"}), 401

        db = SessionLocal()
        try:
            user = db.scalar(select(User).where(User.id == user_id))
            if not user:
                return jsonify({"error": "user_not_found"}), 401
            g.db = db
            g.current_user = user
            return view(*args, **kwargs)
        finally:
            db.close()

    return wrapped_view
