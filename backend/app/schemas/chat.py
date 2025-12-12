"""Chat request and response schemas."""

from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.citation import Citation


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None
    language: Literal["ms", "en"] = "ms"


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str
    citations: List[Citation] = []
    disclaimer: Optional[str] = None
    topics: List[str] = []
    language: str
    message_id: UUID
    conversation_id: UUID


class StreamChunk(BaseModel):
    """Schema for streaming response chunk."""

    type: Literal["text", "citation", "done", "error"]
    content: Optional[str] = None
    citation: Optional[Citation] = None
    message_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class SuggestedQuestion(BaseModel):
    """Schema for suggested follow-up questions."""

    question_ms: str
    question_en: str
    topic: str
