from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from models.comment import Comment
from models.comment_like import CommentLike
from models.post import Post
from models.post_like import PostLike
from models.post_media import PostMedia
from models.user import User


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


def get_post(db: Session, post_id: int) -> Post | None:
    return db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(*_post_load_options())
    )


def create_comment(
    db: Session, author: User, post_id: int, content: str, parent_id: int | None = None
) -> Comment:
    post = get_post(db, post_id)
    if not post:
        raise ValueError("post_not_found")

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
