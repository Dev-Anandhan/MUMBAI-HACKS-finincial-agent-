"""Autonomous action model for automated financial actions."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ActionType(enum.Enum):
    """Autonomous action type enumeration."""
    SAVE_TO_EMERGENCY = "save_to_emergency"
    SAVE_TO_GOAL = "save_to_goal"
    TRANSFER_BETWEEN_ACCOUNTS = "transfer_between_accounts"
    PAUSE_SUBSCRIPTION = "pause_subscription"
    SCHEDULE_BILL_PAYMENT = "schedule_bill_payment"
    DISPUTE_TRANSACTION = "dispute_transaction"
    ADJUST_SPENDING_LIMIT = "adjust_spending_limit"


class ActionStatus(enum.Enum):
    """Action status enumeration."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class ActionRiskLevel(enum.Enum):
    """Action risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AutonomousAction(Base):
    """Model for storing autonomous financial actions."""
    
    __tablename__ = "autonomous_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Action Details
    action_type = Column(Enum(ActionType), nullable=False)
    action_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Action Parameters
    amount = Column(Float, nullable=True)
    source_account = Column(String(100), nullable=True)
    destination_account = Column(String(100), nullable=True)
    action_parameters = Column(JSON, default=dict)  # Additional parameters
    
    # Risk and Safety
    risk_level = Column(Enum(ActionRiskLevel), nullable=False)
    requires_confirmation = Column(Boolean, default=False)
    max_amount = Column(Float, nullable=True)  # Maximum amount for this action type
    
    # Triggering Information
    trigger_nudge_id = Column(Integer, ForeignKey("nudges.id"), nullable=True)
    trigger_prediction_id = Column(Integer, ForeignKey("cashflow_predictions.id"), nullable=True)
    trigger_reason = Column(Text, nullable=False)  # Why this action was triggered
    
    # Execution Details
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results and Feedback
    execution_result = Column(JSON, nullable=True)  # Result of execution
    error_message = Column(Text, nullable=True)
    external_transaction_id = Column(String(100), nullable=True)  # ID from payment provider
    
    # User Interaction
    user_confirmed = Column(Boolean, default=False)
    user_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    user_feedback = Column(JSON, nullable=True)  # User's feedback on the action
    
    # Audit Trail
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String(100), nullable=True)  # User ID or system
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Reversal Information
    can_be_reversed = Column(Boolean, default=True)
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    reversal_transaction_id = Column(String(100), nullable=True)
    
    # Learning and Improvement
    effectiveness_score = Column(Float, nullable=True)  # How effective was this action
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    learned_from = Column(Boolean, default=False)  # Whether we learned from this action
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="autonomous_actions")
    trigger_nudge = relationship("Nudge")
    trigger_prediction = relationship("CashflowPrediction")
    
    def __repr__(self):
        return f"<AutonomousAction(id={self.id}, type={self.action_type}, status={self.status})>"
    
    @property
    def is_low_risk(self):
        """Check if action is low risk."""
        return self.risk_level == ActionRiskLevel.LOW
    
    @property
    def can_execute(self):
        """Check if action can be executed."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        return (
            self.status == ActionStatus.PENDING and
            (self.requires_confirmation and self.user_confirmed) or
            (not self.requires_confirmation) and
            (self.scheduled_for is None or now >= self.scheduled_for)
        )
    
    @property
    def is_reversible(self):
        """Check if action can be reversed."""
        return (
            self.can_be_reversed and
            self.status == ActionStatus.COMPLETED and
            self.reversed_at is None
        )
    
    def execute_action(self, execution_context=None):
        """Execute the autonomous action."""
        # This would integrate with the action executor service
        # For now, just update status
        self.status = ActionStatus.EXECUTING
        self.executed_at = func.now()
        
        # In real implementation, this would call the appropriate service
        # based on action_type and execute the actual financial operation
        
        return True
    
    def reverse_action(self, reason=None):
        """Reverse the autonomous action."""
        if not self.is_reversible:
            return False
        
        self.status = ActionStatus.REVERSED
        self.reversed_at = func.now()
        self.reversal_reason = reason
        
        # In real implementation, this would execute the reversal
        # through the appropriate financial service
        
        return True
    
    def to_dict(self):
        """Convert action to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "action_name": self.action_name,
            "description": self.description,
            "amount": self.amount,
            "risk_level": self.risk_level.value,
            "status": self.status.value,
            "trigger_reason": self.trigger_reason,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "requires_confirmation": self.requires_confirmation,
            "user_confirmed": self.user_confirmed,
            "can_be_reversed": self.can_be_reversed,
            "is_reversible": self.is_reversible,
            "execution_result": self.execution_result,
            "error_message": self.error_message
        }
