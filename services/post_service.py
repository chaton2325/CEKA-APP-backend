from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from models.comment import Comment
from models.post import Post
from models.user import User


def create_post(db: Session, author: User, content: str) -> Post:
    post = Post(author_id=author.id, content=content)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_posts(db: Session) -> list[Post]:
    return list(
        db.scalars(
            select(Post)
            .options(joinedload(Post.author), selectinload(Post.comments))
            .order_by(desc(Post.created_at))
        )
    )


def get_post(db: Session, post_id: int) -> Post | None:
    return db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(joinedload(Post.author), selectinload(Post.comments))
    )


def create_comment(db: Session, author: User, post_id: int, content: str) -> Comment:
    post = get_post(db, post_id)
    if not post:
        raise ValueError("post_not_found")

    comment = Comment(author_id=author.id, post_id=post_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
