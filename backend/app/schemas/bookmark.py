"""Bookmark schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.conversation import MessageResponse


class BookmarkCreate(BaseModel):
    """Schema for creating a bookmark."""

    message_id: UUID
    note: Optional[str] = None
    tags: List[str] = []


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""

    note: Optional[str] = None
    tags: Optional[List[str]] = None


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""

    id: UUID
    message_id: UUID
    message: MessageResponse
    note: Optional[str]
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True
