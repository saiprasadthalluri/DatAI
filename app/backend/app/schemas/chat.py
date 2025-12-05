"""Chat schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime


class ChatMeta(BaseModel):
    """Chat metadata."""
    model: Optional[str] = Field(default="auto", description="Model to use: 'theory-specialist', 'code-specialist', 'math-specialist', or 'auto'")
    mode: Literal["chat", "code", "math"] = "chat"  # Legacy field, kept for compatibility
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class ChatRequest(BaseModel):
    """Chat request."""
    conversation_id: Optional[UUID] = None
    message: str = Field(..., min_length=1, max_length=10000)
    meta: ChatMeta = Field(default_factory=ChatMeta)


class RouterInfo(BaseModel):
    """Router decision info."""
    strategy: Literal["best", "moe"]
    endpoint: str
    confidence: float


class SafetyInfo(BaseModel):
    """Safety check info."""
    input: dict
    output: dict


class ChatResponse(BaseModel):
    """Chat response."""
    assistant_message: str
    conversation_id: UUID
    message_id: UUID
    router: RouterInfo
    safety: SafetyInfo




