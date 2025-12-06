"""Auth schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from .common import BaseSchema


class UserProfile(BaseSchema):
    """User profile schema."""
    id: UUID
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: str
    is_admin: bool
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime


class DevLoginRequest(BaseModel):
    """Dev login request (only in development)."""
    email: EmailStr
    display_name: Optional[str] = None


