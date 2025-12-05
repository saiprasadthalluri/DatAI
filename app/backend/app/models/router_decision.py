"""RouterDecision model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..db.base import Base


class RouterStrategy(str, enum.Enum):
    """Router strategy enum."""
    BEST = "best"
    MOE = "moe"  # Mixture-of-Endpoints


class RouterDecision(Base):
    """RouterDecision model."""
    __tablename__ = "router_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, unique=True, index=True)
    strategy = Column(String(50), nullable=False)  # "best" or "moe"
    selected_endpoint = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    reasons = Column(JSONB, nullable=True)  # Store decision reasoning
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="router_decision")
    
    def __repr__(self):
        return f"<RouterDecision(id={self.id}, strategy={self.strategy}, endpoint={self.selected_endpoint})>"




