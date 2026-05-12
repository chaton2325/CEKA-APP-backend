from flask import Blueprint, g, jsonify, request

from services.notification_service import (
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from utils.auth import jwt_required


notification_bp = Blueprint("notifications", __name__)


def serialize_actor(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "profile_photo_url": user.profile_photo_url,
    }


def serialize_notification(notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.notification_type,
        "actor": serialize_actor(notification.actor),
        "post_id": notification.post_id,
        "comment_id": notification.comment_id,
        "is_read": notification.is_read,
        "created_at": (
            notification.created_at.isoformat() if notification.created_at else None
        ),
    }


@notification_bp.get("/notifications")
@jwt_required
def get_notifications():
    unread_only = (request.args.get("unread_only") or "").lower() in {
        "1",
        "true",
        "yes",
    }
    notifications = list_notifications(g.db, g.current_user, unread_only=unread_only)
    unread_count = sum(1 for notification in notifications if not notification.is_read)
    return jsonify(
        {
            "notifications": [
                serialize_notification(notification) for notification in notifications
            ],
            "unread_count": unread_count,
        }
    )


@notification_bp.put("/notifications/<int:notification_id>/read")
@jwt_required
def read_notification(notification_id: int):
    notification = mark_notification_read(g.db, g.current_user, notification_id)
    if not notification:
        return jsonify({"error": "notification_not_found"}), 404
    return jsonify({"notification": serialize_notification(notification)})


@notification_bp.put("/notifications/read-all")
@jwt_required
def read_all_notifications():
    updated_count = mark_all_notifications_read(g.db, g.current_user)
    return jsonify({"updated_count": updated_count})
