"""Nudge model for proactive financial coaching."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class NudgeType(enum.Enum):
    """Nudge type enumeration."""
    INFORMATIONAL = "informational"  # Just inform user
    ACTIONABLE = "actionable"       # Suggest specific action
    CONTEXTUAL = "contextual"       # Context-aware suggestion
    SOCIAL = "social"              # Social benchmarking


class NudgePriority(enum.Enum):
    """Nudge priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NudgeStatus(enum.Enum):
    """Nudge status enumeration."""
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    ACTED_UPON = "acted_upon"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class Nudge(Base):
    """Model for storing and managing financial nudges."""
    
    __tablename__ = "nudges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Nudge Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    nudge_type = Column(Enum(NudgeType), nullable=False)
    priority = Column(Enum(NudgePriority), default=NudgePriority.MEDIUM)
    
    # Action Details (if actionable)
    suggested_action = Column(JSON, nullable=True)  # Action details
    action_amount = Column(Float, nullable=True)    # Amount if applicable
    action_category = Column(String(100), nullable=True)  # Category of action
    
    # Timing
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Context and Reasoning
    trigger_event = Column(String(100), nullable=True)  # What triggered this nudge
    cashflow_prediction_id = Column(Integer, ForeignKey("cashflow_predictions.id"), nullable=True)
    reasoning = Column(Text, nullable=True)  # Why this nudge was generated
    
    # ML/AI Information
    confidence_score = Column(Float, default=0.0)
    personalization_score = Column(Float, default=0.0)  # How well personalized
    model_version = Column(String(50), default="v1.0")
    
    # Delivery Channels
    delivery_channels = Column(JSON, default=list)  # ["sms", "push", "in_app"]
    preferred_channel = Column(String(20), default="in_app")
    
    # User Interaction
    status = Column(Enum(NudgeStatus), default=NudgeStatus.PENDING)
    user_response = Column(JSON, nullable=True)  # User's response to nudge
    action_taken = Column(Boolean, default=False)
    action_result = Column(JSON, nullable=True)  # Result of action if taken
    
    # Effectiveness Tracking
    engagement_score = Column(Float, default=0.0)  # How engaging was this nudge
    effectiveness_score = Column(Float, nullable=True)  # How effective was it
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="nudges")
    cashflow_prediction = relationship("CashflowPrediction")
    
    def __repr__(self):
        return f"<Nudge(id={self.id}, type={self.nudge_type}, status={self.status})>"
    
    @property
    def is_expired(self):
        """Check if nudge has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_deliverable(self):
        """Check if nudge can be delivered."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return (
            self.status == NudgeStatus.PENDING and
            now >= self.scheduled_for and
            not self.is_expired
        )
    
    def get_personalized_message(self, user_preferences=None):
        """Get personalized version of the message."""
        # This would integrate with the personalization system
        # For now, return the base message
        return self.message
    
    def to_dict(self):
        """Convert nudge to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.nudge_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "scheduled_for": self.scheduled_for.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "suggested_action": self.suggested_action,
            "action_amount": self.action_amount,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "is_expired": self.is_expired,
            "is_deliverable": self.is_deliverable
        }
