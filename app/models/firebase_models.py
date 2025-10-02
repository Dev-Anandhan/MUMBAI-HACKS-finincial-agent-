"""Firebase-compatible data models for the financial agent."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    REFUND = "refund"


class TransactionCategory(str, Enum):
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


class NudgeType(str, Enum):
    """Nudge type enumeration."""
    INFORMATIONAL = "informational"
    ACTIONABLE = "actionable"
    CONTEXTUAL = "contextual"
    SOCIAL = "social"


class NudgePriority(str, Enum):
    """Nudge priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NudgeStatus(str, Enum):
    """Nudge status enumeration."""
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    ACTED_UPON = "acted_upon"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class ActionType(str, Enum):
    """Autonomous action type enumeration."""
    SAVE_TO_EMERGENCY = "save_to_emergency"
    SAVE_TO_GOAL = "save_to_goal"
    TRANSFER_BETWEEN_ACCOUNTS = "transfer_between_accounts"
    PAUSE_SUBSCRIPTION = "pause_subscription"
    SCHEDULE_BILL_PAYMENT = "schedule_bill_payment"
    DISPUTE_TRANSACTION = "dispute_transaction"
    ADJUST_SPENDING_LIMIT = "adjust_spending_limit"


class ActionStatus(str, Enum):
    """Action status enumeration."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class ActionRiskLevel(str, Enum):
    """Action risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PotType(str, Enum):
    """Savings pot type enumeration."""
    EMERGENCY = "emergency"
    GOAL = "goal"
    INVESTMENT = "investment"
    VACATION = "vacation"
    EDUCATION = "education"
    GENERAL = "general"


class PotStatus(str, Enum):
    """Savings pot status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


# Base Model Classes
class BaseFirebaseModel(BaseModel):
    """Base model for Firebase documents."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_firebase_dict(self) -> Dict[str, Any]:
        """Convert to Firebase-compatible dictionary."""
        data = self.dict()
        # Convert datetime objects to ISO strings for Firebase
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_firebase_dict(cls, data: Dict[str, Any]):
        """Create instance from Firebase dictionary."""
        # Convert ISO strings back to datetime objects
        for key, value in data.items():
            if isinstance(value, str) and key.endswith('_at'):
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
        return cls(**data)


class User(BaseFirebaseModel):
    """User model for Firebase."""
    user_id: str = Field(..., description="Unique user identifier")
    phone_number: str = Field(..., description="User's phone number")
    email: Optional[str] = Field(None, description="User's email address")
    
    # Profile Information
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    preferred_language: str = Field(default="en", description="Preferred language")
    timezone: str = Field(default="UTC", description="User's timezone")
    
    # Financial Profile
    income_schedule: Optional[str] = Field(None, description="Income schedule (daily, weekly, etc.)")
    typical_income_amount: Optional[float] = Field(None, description="Typical income amount")
    income_variability: float = Field(default=0.0, description="Income variability (std dev)")
    monthly_commitments: float = Field(default=0.0, description="Monthly financial commitments")
    emergency_fund_target: float = Field(default=0.0, description="Emergency fund target")
    risk_tolerance: str = Field(default="conservative", description="Risk tolerance level")
    
    # Goals
    short_term_goals: List[str] = Field(default_factory=list, description="Short-term goals")
    long_term_goals: List[str] = Field(default_factory=list, description="Long-term goals")
    
    # Preferences
    auto_actions_enabled: bool = Field(default=False, description="Enable autonomous actions")
    max_auto_action_amount: float = Field(default=100.0, description="Max auto action amount")
    notification_preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification settings")
    privacy_settings: Dict[str, Any] = Field(default_factory=dict, description="Privacy settings")
    
    # Agent Learning Data
    user_embedding: Optional[List[float]] = Field(None, description="ML user embedding")
    behavior_patterns: Dict[str, Any] = Field(default_factory=dict, description="Behavior patterns")
    last_income_date: Optional[datetime] = Field(None, description="Last income date")
    last_spending_analysis: Optional[datetime] = Field(None, description="Last spending analysis")
    
    # System Fields
    is_active: bool = Field(default=True, description="User active status")
    is_verified: bool = Field(default=False, description="User verification status")
    last_login: Optional[datetime] = Field(None, description="Last login time")


class Transaction(BaseFirebaseModel):
    """Transaction model for Firebase."""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    user_id: str = Field(..., description="User ID who owns this transaction")
    
    # Transaction Details
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="INR", description="Currency code")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    category: TransactionCategory = Field(default=TransactionCategory.UNKNOWN, description="Transaction category")
    
    # Transaction Metadata
    description: Optional[str] = Field(None, description="Transaction description")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    reference_number: Optional[str] = Field(None, description="Reference number")
    transaction_date: datetime = Field(..., description="Transaction date")
    
    # Source Information
    source_account: Optional[str] = Field(None, description="Source account")
    source_type: Optional[str] = Field(None, description="Source type (bank_api, sms_parse, manual)")
    
    # Classification (ML/AI derived)
    is_essential: Optional[bool] = Field(None, description="Is essential expense")
    is_recurring: bool = Field(default=False, description="Is recurring transaction")
    confidence_score: float = Field(default=0.0, description="ML confidence score")
    ml_features: Dict[str, Any] = Field(default_factory=dict, description="ML features")
    
    # Location and Context
    location: Optional[str] = Field(None, description="Transaction location")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    
    # System Fields
    is_verified: bool = Field(default=False, description="Transaction verification status")
    is_deleted: bool = Field(default=False, description="Transaction deletion status")


class CashflowPrediction(BaseFirebaseModel):
    """Cashflow prediction model for Firebase."""
    prediction_id: str = Field(..., description="Unique prediction identifier")
    user_id: str = Field(..., description="User ID")
    
    # Prediction Details
    prediction_date: datetime = Field(..., description="When prediction was made")
    forecast_start_date: datetime = Field(..., description="Forecast start date")
    forecast_end_date: datetime = Field(..., description="Forecast end date")
    
    # Predicted Values
    predicted_balance: float = Field(..., description="Predicted balance")
    confidence_level: float = Field(..., description="Prediction confidence")
    shortfall_probability: float = Field(default=0.0, description="Shortfall probability")
    shortfall_amount: Optional[float] = Field(None, description="Predicted shortfall amount")
    
    # Detailed Forecast
    daily_forecasts: List[Dict[str, Any]] = Field(default_factory=list, description="Daily forecasts")
    
    # Risk Metrics
    liquidity_risk_score: float = Field(default=0.0, description="Liquidity risk score")
    income_uncertainty: float = Field(default=0.0, description="Income uncertainty")
    expense_volatility: float = Field(default=0.0, description="Expense volatility")
    
    # Model Information
    model_version: str = Field(default="v1.0", description="Model version")
    model_features: Dict[str, Any] = Field(default_factory=dict, description="Model features")
    prediction_reasoning: Optional[str] = Field(None, description="Prediction reasoning")
    
    # Validation
    is_validated: bool = Field(default=False, description="Prediction validation status")
    actual_balance: Optional[float] = Field(None, description="Actual balance")
    prediction_accuracy: Optional[float] = Field(None, description="Prediction accuracy")


class Nudge(BaseFirebaseModel):
    """Nudge model for Firebase."""
    nudge_id: str = Field(..., description="Unique nudge identifier")
    user_id: str = Field(..., description="User ID")
    
    # Nudge Content
    title: str = Field(..., description="Nudge title")
    message: str = Field(..., description="Nudge message")
    nudge_type: NudgeType = Field(..., description="Type of nudge")
    priority: NudgePriority = Field(default=NudgePriority.MEDIUM, description="Nudge priority")
    
    # Action Details
    suggested_action: Optional[Dict[str, Any]] = Field(None, description="Suggested action")
    action_amount: Optional[float] = Field(None, description="Action amount")
    action_category: Optional[str] = Field(None, description="Action category")
    
    # Timing
    scheduled_for: datetime = Field(..., description="When to deliver nudge")
    expires_at: Optional[datetime] = Field(None, description="Nudge expiration")
    delivered_at: Optional[datetime] = Field(None, description="When nudge was delivered")
    
    # Context and Reasoning
    trigger_event: Optional[str] = Field(None, description="What triggered this nudge")
    cashflow_prediction_id: Optional[str] = Field(None, description="Related prediction ID")
    reasoning: Optional[str] = Field(None, description="Why this nudge was generated")
    
    # ML/AI Information
    confidence_score: float = Field(default=0.0, description="Nudge confidence")
    personalization_score: float = Field(default=0.0, description="Personalization score")
    model_version: str = Field(default="v1.0", description="Model version")
    
    # Delivery Channels
    delivery_channels: List[str] = Field(default_factory=list, description="Delivery channels")
    preferred_channel: str = Field(default="in_app", description="Preferred channel")
    
    # User Interaction
    status: NudgeStatus = Field(default=NudgeStatus.PENDING, description="Nudge status")
    user_response: Optional[Dict[str, Any]] = Field(None, description="User response")
    action_taken: bool = Field(default=False, description="Action taken status")
    action_result: Optional[Dict[str, Any]] = Field(None, description="Action result")
    
    # Effectiveness Tracking
    engagement_score: float = Field(default=0.0, description="Engagement score")
    effectiveness_score: Optional[float] = Field(None, description="Effectiveness score")
    user_satisfaction: Optional[int] = Field(None, description="User satisfaction rating")


class AutonomousAction(BaseFirebaseModel):
    """Autonomous action model for Firebase."""
    action_id: str = Field(..., description="Unique action identifier")
    user_id: str = Field(..., description="User ID")
    
    # Action Details
    action_type: ActionType = Field(..., description="Type of action")
    action_name: str = Field(..., description="Action name")
    description: str = Field(..., description="Action description")
    
    # Action Parameters
    amount: Optional[float] = Field(None, description="Action amount")
    source_account: Optional[str] = Field(None, description="Source account")
    destination_account: Optional[str] = Field(None, description="Destination account")
    action_parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    
    # Risk and Safety
    risk_level: ActionRiskLevel = Field(..., description="Action risk level")
    requires_confirmation: bool = Field(default=False, description="Requires confirmation")
    max_amount: Optional[float] = Field(None, description="Maximum amount")
    
    # Triggering Information
    trigger_nudge_id: Optional[str] = Field(None, description="Triggering nudge ID")
    trigger_prediction_id: Optional[str] = Field(None, description="Triggering prediction ID")
    trigger_reason: str = Field(..., description="Why this action was triggered")
    
    # Execution Details
    status: ActionStatus = Field(default=ActionStatus.PENDING, description="Action status")
    scheduled_for: Optional[datetime] = Field(None, description="When to execute")
    executed_at: Optional[datetime] = Field(None, description="When executed")
    completed_at: Optional[datetime] = Field(None, description="When completed")
    
    # Results and Feedback
    execution_result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error_message: Optional[str] = Field(None, description="Error message")
    external_transaction_id: Optional[str] = Field(None, description="External transaction ID")
    
    # User Interaction
    user_confirmed: bool = Field(default=False, description="User confirmation")
    user_confirmed_at: Optional[datetime] = Field(None, description="Confirmation time")
    user_feedback: Optional[Dict[str, Any]] = Field(None, description="User feedback")
    
    # Audit Trail
    approval_required: bool = Field(default=False, description="Approval required")
    approved_by: Optional[str] = Field(None, description="Approved by")
    approved_at: Optional[datetime] = Field(None, description="Approval time")
    
    # Reversal Information
    can_be_reversed: bool = Field(default=True, description="Can be reversed")
    reversed_at: Optional[datetime] = Field(None, description="Reversal time")
    reversal_reason: Optional[str] = Field(None, description="Reversal reason")
    reversal_transaction_id: Optional[str] = Field(None, description="Reversal transaction ID")
    
    # Learning and Improvement
    effectiveness_score: Optional[float] = Field(None, description="Effectiveness score")
    user_satisfaction: Optional[int] = Field(None, description="User satisfaction")
    learned_from: bool = Field(default=False, description="Learned from this action")


class SavingsPot(BaseFirebaseModel):
    """Savings pot model for Firebase."""
    pot_id: str = Field(..., description="Unique pot identifier")
    user_id: str = Field(..., description="User ID")
    
    # Pot Details
    name: str = Field(..., description="Pot name")
    description: Optional[str] = Field(None, description="Pot description")
    pot_type: PotType = Field(..., description="Type of pot")
    
    # Financial Details
    target_amount: Optional[float] = Field(None, description="Target amount")
    current_amount: float = Field(default=0.0, description="Current amount")
    currency: str = Field(default="INR", description="Currency")
    
    # Goal Timeline
    target_date: Optional[datetime] = Field(None, description="Target date")
    
    # Savings Strategy
    monthly_contribution: Optional[float] = Field(None, description="Monthly contribution")
    contribution_frequency: str = Field(default="monthly", description="Contribution frequency")
    auto_contribute: bool = Field(default=False, description="Auto contribute")
    
    # Status and Settings
    status: PotStatus = Field(default=PotStatus.ACTIVE, description="Pot status")
    is_locked: bool = Field(default=False, description="Is locked")
    is_emergency_accessible: bool = Field(default=False, description="Emergency accessible")
    
    # Investment Settings
    investment_risk_level: Optional[str] = Field(None, description="Investment risk level")
    investment_strategy: Dict[str, Any] = Field(default_factory=dict, description="Investment strategy")
    
    # Analytics
    total_contributions: float = Field(default=0.0, description="Total contributions")
    total_withdrawals: float = Field(default=0.0, description="Total withdrawals")
    interest_earned: float = Field(default=0.0, description="Interest earned")
    last_contribution_date: Optional[datetime] = Field(None, description="Last contribution")
    last_withdrawal_date: Optional[datetime] = Field(None, description="Last withdrawal")
    
    # Progress Tracking
    progress_percentage: float = Field(default=0.0, description="Progress percentage")
    days_to_target: Optional[int] = Field(None, description="Days to target")
    projected_completion_date: Optional[datetime] = Field(None, description="Projected completion")
