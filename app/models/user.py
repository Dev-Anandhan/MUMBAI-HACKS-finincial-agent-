"""User model for the financial agent."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model representing a financial agent user."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    
    # Profile Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    
    # Financial Profile
    income_schedule = Column(String(50))  # daily, weekly, bi-weekly, monthly, irregular
    typical_income_amount = Column(Float, nullable=True)
    income_variability = Column(Float, default=0.0)  # Standard deviation
    monthly_commitments = Column(Float, default=0.0)
    emergency_fund_target = Column(Float, default=0.0)
    risk_tolerance = Column(String(20), default="conservative")  # conservative, moderate, aggressive
    
    # Goals
    short_term_goals = Column(JSON, default=list)  # List of short-term financial goals
    long_term_goals = Column(JSON, default=list)   # List of long-term financial goals
    
    # Preferences
    auto_actions_enabled = Column(Boolean, default=False)
    max_auto_action_amount = Column(Float, default=100.0)
    notification_preferences = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    
    # Agent Learning Data
    user_embedding = Column(JSON, nullable=True)  # ML feature vector
    behavior_patterns = Column(JSON, default=dict)
    last_income_date = Column(DateTime, nullable=True)
    last_spending_analysis = Column(DateTime, nullable=True)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    cashflow_predictions = relationship("CashflowPrediction", back_populates="user")
    nudges = relationship("Nudge", back_populates="user")
    autonomous_actions = relationship("AutonomousAction", back_populates="user")
    savings_pots = relationship("SavingsPot", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone_number})>"
    
    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.phone_number
    
    def get_income_variability_metric(self):
        """Calculate income variability as a percentage."""
        if self.typical_income_amount and self.income_variability:
            return (self.income_variability / self.typical_income_amount) * 100
        return 0.0
    
    def is_high_variability_user(self):
        """Check if user has high income variability (>30%)."""
        return self.get_income_variability_metric() > 30.0
