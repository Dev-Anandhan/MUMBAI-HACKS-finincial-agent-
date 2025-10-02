"""Cashflow prediction model for ML predictions."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CashflowPrediction(Base):
    """Model for storing cashflow predictions and forecasts."""
    
    __tablename__ = "cashflow_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prediction Details
    prediction_date = Column(DateTime(timezone=True), nullable=False)  # When prediction was made
    forecast_start_date = Column(DateTime(timezone=True), nullable=False)  # Start of forecast period
    forecast_end_date = Column(DateTime(timezone=True), nullable=False)  # End of forecast period
    
    # Predicted Values
    predicted_balance = Column(Float, nullable=False)  # Predicted balance at end date
    confidence_level = Column(Float, nullable=False)  # 0.0 to 1.0
    shortfall_probability = Column(Float, default=0.0)  # Probability of negative balance
    shortfall_amount = Column(Float, nullable=True)  # Predicted shortfall amount if any
    
    # Detailed Forecast (JSON array of daily predictions)
    daily_forecasts = Column(JSON, default=list)  # [{"date": "2024-01-01", "balance": 1000, "confidence": 0.8}]
    
    # Risk Metrics
    liquidity_risk_score = Column(Float, default=0.0)  # 0.0 to 1.0
    income_uncertainty = Column(Float, default=0.0)  # Income variability impact
    expense_volatility = Column(Float, default=0.0)  # Expense variability impact
    
    # Model Information
    model_version = Column(String(50), default="v1.0")
    model_features = Column(JSON, default=dict)  # Features used for prediction
    prediction_reasoning = Column(Text, nullable=True)  # Human-readable explanation
    
    # Validation
    is_validated = Column(Boolean, default=False)  # Whether actual outcome was recorded
    actual_balance = Column(Float, nullable=True)  # Actual balance at end date
    prediction_accuracy = Column(Float, nullable=True)  # Accuracy score
    
    # System Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cashflow_predictions")
    
    def __repr__(self):
        return f"<CashflowPrediction(id={self.id}, user_id={self.user_id}, confidence={self.confidence_level})>"
    
    @property
    def is_high_risk(self):
        """Check if prediction indicates high risk."""
        return self.shortfall_probability > 0.7 or self.liquidity_risk_score > 0.8
    
    @property
    def days_until_shortfall(self):
        """Calculate days until predicted shortfall."""
        if not self.shortfall_probability > 0.5:
            return None
        
        # Find first day with negative predicted balance
        for day_forecast in self.daily_forecasts:
            if day_forecast.get("balance", 0) < 0:
                forecast_date = day_forecast.get("date")
                if forecast_date:
                    from datetime import datetime
                    try:
                        forecast_date = datetime.fromisoformat(forecast_date)
                        days_diff = (forecast_date - self.prediction_date).days
                        return max(0, days_diff)
                    except (ValueError, TypeError):
                        continue
        return None
    
    def get_risk_level(self):
        """Get human-readable risk level."""
        if self.shortfall_probability > 0.8:
            return "critical"
        elif self.shortfall_probability > 0.6:
            return "high"
        elif self.shortfall_probability > 0.4:
            return "medium"
        else:
            return "low"
    
    def to_dict(self):
        """Convert prediction to dictionary."""
        return {
            "id": self.id,
            "prediction_date": self.prediction_date.isoformat(),
            "forecast_period": {
                "start": self.forecast_start_date.isoformat(),
                "end": self.forecast_end_date.isoformat()
            },
            "predicted_balance": self.predicted_balance,
            "confidence_level": self.confidence_level,
            "shortfall_probability": self.shortfall_probability,
            "shortfall_amount": self.shortfall_amount,
            "risk_level": self.get_risk_level(),
            "days_until_shortfall": self.days_until_shortfall,
            "daily_forecasts": self.daily_forecasts,
            "prediction_reasoning": self.prediction_reasoning
        }
