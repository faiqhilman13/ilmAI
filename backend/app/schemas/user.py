"""User schemas."""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    display_name: Optional[str] = None
    preferred_language: Literal["ms", "en"] = "ms"
    preferred_madhab: str = "shafii"


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user."""

    display_name: Optional[str] = None
    preferred_language: Optional[Literal["ms", "en"]] = None
    preferred_madhab: Optional[str] = None


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
