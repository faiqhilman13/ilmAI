"""Conversation and message schemas."""

from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.citation import Citation


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: Optional[List[Citation]] = None
    disclaimer: Optional[str] = None
    topics: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: Optional[str] = None
    language: Literal["ms", "en"] = "ms"


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID
    title: Optional[str]
    language: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    """Schema for conversation list item (without messages)."""

    id: UUID
    title: Optional[str]
    language: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True
