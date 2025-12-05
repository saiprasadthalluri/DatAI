"""Common schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class HealthResponse(BaseSchema):
    """Health check response."""
    status: str
    database: Optional[str] = None
    redis: Optional[str] = None
    safety: Optional[str] = None




