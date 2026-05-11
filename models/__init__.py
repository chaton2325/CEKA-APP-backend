from models.base import Base


def load_models() -> None:
    from models.comment import Comment  # noqa: F401
    from models.post import Post  # noqa: F401
    from models.user import User  # noqa: F401


__all__ = ["Base", "load_models"]
