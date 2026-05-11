from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

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
