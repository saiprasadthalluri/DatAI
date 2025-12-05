"""Conversation schemas."""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from .common import BaseSchema


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Create conversation request."""
    pass


class ConversationUpdate(BaseModel):
    """Update conversation request."""
    title: Optional[str] = None
    archived: Optional[bool] = None


class ConversationResponse(BaseSchema):
    """Conversation response."""
    id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]


class MessageResponse(BaseSchema):
    """Message response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    latency_ms: Optional[int]
    safety_labels: Optional[dict]
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    """Conversation detail with messages."""
    messages: list[MessageResponse] = []




