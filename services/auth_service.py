from datetime import datetime, timedelta
from secrets import randbelow

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models.comment import Comment
from models.data_deletion_request import DataDeletionRequest
from models.notification import Notification
from models.password_reset_code import PasswordResetCode
from models.post import Post
from models.user import User


def register_user(db: Session, username: str, email: str, password: str) -> User:
    existing_user = db.scalar(
        select(User).where(or_(User.username == username, User.email == email))
    )
    if existing_user:
        raise ValueError("username_or_email_already_exists")

    user = User(
        username=username,
        email=email.lower(),
        password_hash=generate_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not check_password_hash(user.password_hash, password):
        return None
    return user


def create_password_reset_code(db: Session, email: str) -> str | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user:
        return None

    code = f"{randbelow(1_000_000):06d}"
    reset_code = PasswordResetCode(
        user_id=user.id,
        code_hash=generate_password_hash(code),
        expires_at=datetime.utcnow()
        + timedelta(minutes=Config.PASSWORD_RESET_CODE_EXPIRATION_MINUTES),
    )
    db.add(reset_code)
    db.commit()
    return code


def reset_password_with_code(
    db: Session, email: str, code: str, new_password: str
) -> bool:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user:
        return False

    reset_code = db.scalar(
        select(PasswordResetCode)
        .where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
        )
        .order_by(desc(PasswordResetCode.created_at))
    )
    if not reset_code:
        return False

    if reset_code.expires_at < datetime.utcnow():
        return False

    if not check_password_hash(reset_code.code_hash, code):
        return False

    user.password_hash = generate_password_hash(new_password)
    reset_code.used_at = datetime.utcnow()
    db.commit()
    return True


def change_user_password(
    db: Session, user: User, current_password: str, new_password: str
) -> bool:
    if not check_password_hash(user.password_hash, current_password):
        return False

    user.password_hash = generate_password_hash(new_password)
    db.commit()
    return True


def update_user_profile(
    db: Session,
    user: User,
    username: str | None = None,
    bio: str | None = None,
    profile_photo_url: str | None = None,
    banner_photo_url: str | None = None,
) -> User:
    if username and username != user.username:
        existing_user = db.scalar(select(User).where(User.username == username))
        if existing_user:
            raise ValueError("username_already_exists")
        user.username = username

    if bio is not None:
        user.bio = bio
    if profile_photo_url is not None:
        user.profile_photo_url = profile_photo_url
    if banner_photo_url is not None:
        user.banner_photo_url = banner_photo_url

    db.commit()
    db.refresh(user)
    return user


def request_data_deletion(
    db: Session, user: User, reason: str | None = None
) -> DataDeletionRequest:
    deletion_request = DataDeletionRequest(
        requester_user_id=user.id,
        requester_username=user.username,
        requester_email=user.email,
        reason=reason,
    )
    db.add(deletion_request)
    db.commit()
    db.refresh(deletion_request)
    return deletion_request


def delete_user_account(db: Session, user: User, current_password: str) -> bool:
    if not check_password_hash(user.password_hash, current_password):
        return False

    post_ids = list(db.scalars(select(Post.id).where(Post.author_id == user.id)))
    comment_ids = list(
        db.scalars(
            select(Comment.id).where(
                or_(Comment.author_id == user.id, Comment.post_id.in_(post_ids))
            )
        )
    )

    notification_filters = [
        Notification.actor_id == user.id,
        Notification.recipient_id == user.id,
    ]
    if post_ids:
        notification_filters.append(Notification.post_id.in_(post_ids))
    if comment_ids:
        notification_filters.append(Notification.comment_id.in_(comment_ids))

    for notification in list(
        db.scalars(select(Notification).where(or_(*notification_filters)))
    ):
        db.delete(notification)

    for reset_code in list(
        db.scalars(select(PasswordResetCode).where(PasswordResetCode.user_id == user.id))
    ):
        db.delete(reset_code)

    db.delete(user)
    db.commit()
    return True
