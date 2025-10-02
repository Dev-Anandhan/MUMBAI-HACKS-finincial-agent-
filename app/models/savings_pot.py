"""Savings pot model for goal-based savings."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PotType(enum.Enum):
    """Savings pot type enumeration."""
    EMERGENCY = "emergency"
    GOAL = "goal"
    INVESTMENT = "investment"
    VACATION = "vacation"
    EDUCATION = "education"
    GENERAL = "general"


class PotStatus(enum.Enum):
    """Savings pot status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SavingsPot(Base):
    """Model for savings pots/goals."""
    
    __tablename__ = "savings_pots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Pot Details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    pot_type = Column(Enum(PotType), nullable=False)
    
    # Financial Details
    target_amount = Column(Float, nullable=True)  # Target amount to save
    current_amount = Column(Float, default=0.0)   # Current amount saved
    currency = Column(String(3), default="INR")
    
    # Goal Timeline
    target_date = Column(DateTime(timezone=True), nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Savings Strategy
    monthly_contribution = Column(Float, nullable=True)  # Suggested monthly contribution
    contribution_frequency = Column(String(20), default="monthly")  # daily, weekly, monthly
    auto_contribute = Column(Boolean, default=False)  # Auto-contribute from income
    
    # Status and Settings
    status = Column(Enum(PotStatus), default=PotStatus.ACTIVE)
    is_locked = Column(Boolean, default=False)  # Locked until target date
    is_emergency_accessible = Column(Boolean, default=False)  # Can be used for emergencies
    
    # Investment Settings (for investment pots)
    investment_risk_level = Column(String(20), nullable=True)  # conservative, moderate, aggressive
    investment_strategy = Column(JSON, default=dict)  # Investment allocation strategy
    
    # Analytics
    total_contributions = Column(Float, default=0.0)
    total_withdrawals = Column(Float, default=0.0)
    interest_earned = Column(Float, default=0.0)
    last_contribution_date = Column(DateTime(timezone=True), nullable=True)
    last_withdrawal_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress Tracking
    progress_percentage = Column(Float, default=0.0)  # Percentage of target achieved
    days_to_target = Column(Integer, nullable=True)  # Days remaining to target date
    projected_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="savings_pots")
    
    def __repr__(self):
        return f"<SavingsPot(id={self.id}, name={self.name}, amount={self.current_amount})>"
    
    @property
    def is_fully_funded(self):
        """Check if pot has reached its target."""
        if not self.target_amount:
            return False
        return self.current_amount >= self.target_amount
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach target."""
        if not self.target_amount:
            return 0.0
        return max(0.0, self.target_amount - self.current_amount)
    
    def calculate_progress_percentage(self):
        """Calculate progress percentage towards target."""
        if not self.target_amount or self.target_amount == 0:
            return 0.0
        return min(100.0, (self.current_amount / self.target_amount) * 100)
    
    def add_contribution(self, amount: float, source: str = None):
        """Add a contribution to the pot."""
        self.current_amount += amount
        self.total_contributions += amount
        self.last_contribution_date = func.now()
        self.progress_percentage = self.calculate_progress_percentage()
        
        # Check if target is reached
        if self.is_fully_funded and self.status == PotStatus.ACTIVE:
            self.status = PotStatus.COMPLETED
    
    def make_withdrawal(self, amount: float, reason: str = None):
        """Make a withdrawal from the pot."""
        if amount > self.current_amount:
            raise ValueError("Insufficient funds in pot")
        
        self.current_amount -= amount
        self.total_withdrawals += amount
        self.last_withdrawal_date = func.now()
        self.progress_percentage = self.calculate_progress_percentage()
    
    def get_suggested_monthly_contribution(self):
        """Calculate suggested monthly contribution to reach target."""
        if not self.target_date or not self.target_amount:
            return None
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        months_remaining = max(1, (self.target_date - now).days / 30.44)  # Average days per month
        
        return self.remaining_amount / months_remaining
    
    def to_dict(self):
        """Convert pot to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.pot_type.value,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "currency": self.currency,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "status": self.status.value,
            "is_locked": self.is_locked,
            "progress_percentage": self.progress_percentage,
            "remaining_amount": self.remaining_amount,
            "is_fully_funded": self.is_fully_funded,
            "monthly_contribution": self.monthly_contribution,
            "auto_contribute": self.auto_contribute,
            "total_contributions": self.total_contributions,
            "total_withdrawals": self.total_withdrawals,
            "interest_earned": self.interest_earned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
