from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from models.notification import Notification
from models.user import User


def create_notification(
    db: Session,
    recipient_id: int,
    actor_id: int,
    notification_type: str,
    post_id: int | None = None,
    comment_id: int | None = None,
) -> Notification | None:
    if recipient_id == actor_id:
        return None

    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        post_id=post_id,
        comment_id=comment_id,
    )
    db.add(notification)
    return notification


def list_notifications(
    db: Session, user: User, unread_only: bool = False
) -> list[Notification]:
    query = (
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .options(joinedload(Notification.actor))
        .order_by(desc(Notification.created_at))
    )
    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    return list(db.scalars(query))


def mark_notification_read(
    db: Session, user: User, notification_id: int
) -> Notification | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == user.id,
        )
    )
    if not notification:
        return None

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_notifications_read(db: Session, user: User) -> int:
    notifications = list(
        db.scalars(
            select(Notification).where(
                Notification.recipient_id == user.id,
                Notification.is_read.is_(False),
            )
        )
    )
    for notification in notifications:
        notification.is_read = True

    db.commit()
    return len(notifications)
