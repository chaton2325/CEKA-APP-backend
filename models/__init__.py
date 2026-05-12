from models.base import Base


def load_models() -> None:
    from models.comment import Comment  # noqa: F401
    from models.comment_like import CommentLike  # noqa: F401
    from models.data_deletion_request import DataDeletionRequest  # noqa: F401
    from models.notification import Notification  # noqa: F401
    from models.password_reset_code import PasswordResetCode  # noqa: F401
    from models.post import Post  # noqa: F401
    from models.post_like import PostLike  # noqa: F401
    from models.post_media import PostMedia  # noqa: F401
    from models.user import User  # noqa: F401


__all__ = ["Base", "load_models"]
