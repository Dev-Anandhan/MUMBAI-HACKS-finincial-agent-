"""Transaction model for financial data."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionType(enum.Enum):
    """Transaction type enumeration."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    REFUND = "refund"


class TransactionCategory(enum.Enum):
    """Transaction category enumeration."""
    # Income categories
    GIG_INCOME = "gig_income"
    SALARY = "salary"
    BONUS = "bonus"
    INVESTMENT_RETURN = "investment_return"
    REFUND = "refund"
    
    # Essential expenses
    RENT = "rent"
    UTILITIES = "utilities"
    GROCERIES = "groceries"
    TRANSPORT = "transport"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    DEBT_PAYMENT = "debt_payment"
    
    # Discretionary expenses
    ENTERTAINMENT = "entertainment"
    DINING = "dining"
    SHOPPING = "shopping"
    SUBSCRIPTIONS = "subscriptions"
    TRAVEL = "travel"
    
    # Other
    UNKNOWN = "unknown"
    TRANSFER = "transfer"


class Transaction(Base):
    """Transaction model for financial transactions."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Transaction Details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(Enum(TransactionCategory), default=TransactionCategory.UNKNOWN)
    
    # Transaction Metadata
    description = Column(Text, nullable=True)
    merchant_name = Column(String(255), nullable=True)
    reference_number = Column(String(100), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    
    # Source Information
    source_account = Column(String(100), nullable=True)  # Bank account, wallet, etc.
    source_type = Column(String(50), nullable=True)  # bank_api, sms_parse, manual
    
    # Classification (ML/AI derived)
    is_essential = Column(Boolean, nullable=True)  # True for essential expenses
    is_recurring = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)  # ML confidence in classification
    ml_features = Column(JSON, default=dict)  # Features used for classification
    
    # Location and Context
    location = Column(String(255), nullable=True)
    device_info = Column(JSON, default=dict)
    
    # System Fields
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.transaction_type})>"
    
    @property
    def is_income(self):
        """Check if transaction is income."""
        return self.transaction_type == TransactionType.INCOME
    
    @property
    def is_expense(self):
        """Check if transaction is expense."""
        return self.transaction_type == TransactionType.EXPENSE
    
    @property
    def signed_amount(self):
        """Get signed amount (positive for income, negative for expense)."""
        if self.is_income:
            return self.amount
        elif self.is_expense:
            return -self.amount
        return self.amount  # For transfers, keep original amount
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "type": self.transaction_type.value,
            "category": self.category.value,
            "description": self.description,
            "merchant_name": self.merchant_name,
            "transaction_date": self.transaction_date.isoformat(),
            "is_essential": self.is_essential,
            "is_recurring": self.is_recurring,
            "confidence_score": self.confidence_score
        }
