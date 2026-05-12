from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from models.comment import Comment
from models.comment_like import CommentLike
from models.notification import Notification
from models.post import Post
from models.post_like import PostLike
from models.post_media import PostMedia
from models.user import User
from services.notification_service import create_notification


def create_post(db: Session, author: User, content: str, media_files: list[dict]) -> Post:
    post = Post(author_id=author.id, content=content)
    db.add(post)
    db.flush()

    for position, media_file in enumerate(media_files):
        db.add(
            PostMedia(
                post_id=post.id,
                url=media_file["url"],
                media_type=media_file["media_type"],
                filename=media_file.get("filename"),
                position=position,
            )
        )

    db.commit()
    db.refresh(post)
    return post


def _post_load_options():
    return (
        joinedload(Post.author),
        selectinload(Post.media),
        selectinload(Post.likes).joinedload(PostLike.user),
        selectinload(Post.comments).joinedload(Comment.author),
        selectinload(Post.comments).selectinload(Comment.likes).joinedload(CommentLike.user),
        selectinload(Post.comments).selectinload(Comment.replies).joinedload(Comment.author),
        selectinload(Post.comments)
        .selectinload(Comment.replies)
        .selectinload(Comment.likes)
        .joinedload(CommentLike.user),
    )


def list_posts(db: Session) -> list[Post]:
    return list(
        db.scalars(
            select(Post)
            .options(*_post_load_options())
            .order_by(desc(Post.created_at))
        )
    )


def list_user_posts(db: Session, user_id: int) -> list[Post]:
    return list(
        db.scalars(
            select(Post)
            .where(Post.author_id == user_id)
            .options(*_post_load_options())
            .order_by(desc(Post.created_at))
        )
    )


def get_post(db: Session, post_id: int) -> Post | None:
    return db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(*_post_load_options())
    )


def update_post(
    db: Session,
    user: User,
    post_id: int,
    content: str | None = None,
    media_files: list[dict] | None = None,
    replace_media: bool = False,
) -> Post:
    post = get_post(db, post_id)
    if not post:
        raise ValueError("post_not_found")
    if post.author_id != user.id:
        raise PermissionError("forbidden")

    if content is not None:
        post.content = content

    if replace_media:
        for media in list(post.media):
            db.delete(media)
        db.flush()

    if media_files:
        start_position = 0 if replace_media else len(post.media)
        for index, media_file in enumerate(media_files):
            db.add(
                PostMedia(
                    post_id=post.id,
                    url=media_file["url"],
                    media_type=media_file["media_type"],
                    filename=media_file.get("filename"),
                    position=start_position + index,
                )
            )

    existing_media_count = 0 if replace_media else len(post.media)
    new_media_count = len(media_files or [])
    if not post.content.strip() and existing_media_count + new_media_count == 0:
        raise ValueError("content_or_media_required")

    db.commit()
    return get_post(db, post_id)


def delete_post(db: Session, user: User, post_id: int) -> None:
    post = db.get(Post, post_id)
    if not post:
        raise ValueError("post_not_found")
    if post.author_id != user.id:
        raise PermissionError("forbidden")

    for notification in list(
        db.scalars(select(Notification).where(Notification.post_id == post_id))
    ):
        db.delete(notification)
    db.delete(post)
    db.commit()


def create_comment(
    db: Session, author: User, post_id: int, content: str, parent_id: int | None = None
) -> Comment:
    post = get_post(db, post_id)
    if not post:
        raise ValueError("post_not_found")

    parent = None
    if parent_id is not None:
        parent = db.get(Comment, parent_id)
        if not parent or parent.post_id != post_id:
            raise ValueError("comment_not_found")

    comment = Comment(
        author_id=author.id,
        post_id=post_id,
        content=content,
        parent_id=parent_id,
    )
    db.add(comment)
    db.flush()

    recipient_id = parent.author_id if parent else post.author_id
    notification_type = "comment_reply" if parent else "post_comment"
    create_notification(
        db,
        recipient_id=recipient_id,
        actor_id=author.id,
        notification_type=notification_type,
        post_id=post_id,
        comment_id=comment.id,
    )

    db.commit()
    db.refresh(comment)
    return comment


def like_post(db: Session, user: User, post_id: int) -> PostLike:
    post = get_post(db, post_id)
    if not post:
        raise ValueError("post_not_found")

    existing_like = db.scalar(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user.id)
    )
    if existing_like:
        return existing_like

    like = PostLike(post_id=post_id, user_id=user.id)
    db.add(like)
    create_notification(
        db,
        recipient_id=post.author_id,
        actor_id=user.id,
        notification_type="post_like",
        post_id=post_id,
    )
    db.commit()
    db.refresh(like)
    return like


def unlike_post(db: Session, user: User, post_id: int) -> bool:
    like = db.scalar(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user.id)
    )
    if not like:
        if not db.get(Post, post_id):
            raise ValueError("post_not_found")
        return False

    db.delete(like)
    db.commit()
    return True


def like_comment(db: Session, user: User, comment_id: int) -> CommentLike:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise ValueError("comment_not_found")

    existing_like = db.scalar(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id,
        )
    )
    if existing_like:
        return existing_like

    like = CommentLike(comment_id=comment_id, user_id=user.id)
    db.add(like)
    create_notification(
        db,
        recipient_id=comment.author_id,
        actor_id=user.id,
        notification_type="comment_like",
        post_id=comment.post_id,
        comment_id=comment_id,
    )
    db.commit()
    db.refresh(like)
    return like


def unlike_comment(db: Session, user: User, comment_id: int) -> bool:
    like = db.scalar(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id,
        )
    )
    if not like:
        if not db.get(Comment, comment_id):
            raise ValueError("comment_not_found")
        return False

    db.delete(like)
    db.commit()
    return True
