from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DataDeletionRequest(Base):
    __tablename__ = "data_deletion_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requester_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requester_username: Mapped[str] = mapped_column(String(80), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
