"""Knowledge source and chunk models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class KnowledgeSource(Base):
    """Knowledge source model (Quran, Hadith collections, etc.)."""

    __tablename__ = "knowledge_sources"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_metadata: Mapped[dict | None] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="source")


class KnowledgeChunk(Base):
    """Knowledge chunk model with vector embedding."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="SET NULL")
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    text_arabic: Mapped[str | None] = mapped_column(Text)
    text_translation: Mapped[str | None] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    chunk_index: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    source = relationship("KnowledgeSource", back_populates="chunks")
