"""Bookmark model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Bookmark(Base):
    """Bookmark model."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "message_id", name="uq_user_message"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    message = relationship("Message", back_populates="bookmarks")
