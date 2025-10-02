"""Cashflow prediction API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import CashflowPrediction
from app.services.cashflow_predictor import CashflowPredictor

router = APIRouter()


class PredictionResponse(BaseModel):
    """Prediction response model."""
    prediction_id: str
    user_id: str
    prediction_date: str
    forecast_start_date: str
    forecast_end_date: str
    predicted_balance: float
    confidence_level: float
    shortfall_probability: float
    shortfall_amount: Optional[float]
    daily_forecasts: List[dict]
    liquidity_risk_score: float
    income_uncertainty: float
    expense_volatility: float
    model_version: str
    prediction_reasoning: Optional[str]


def get_cashflow_predictor() -> CashflowPredictor:
    """Get cashflow predictor instance."""
    return CashflowPredictor()


@router.post("/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    days_ahead: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    predictor: CashflowPredictor = Depends(get_cashflow_predictor)
):
    """Generate a new cashflow prediction."""
    try:
        prediction = await predictor.predict_cashflow(
            current_user["user_id"],
            days_ahead=days_ahead
        )
        return PredictionResponse(**prediction.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate prediction: {str(e)}"
        )


@router.get("/latest", response_model=PredictionResponse)
async def get_latest_prediction(
    current_user: dict = Depends(get_current_user),
    predictor: CashflowPredictor = Depends(get_cashflow_predictor)
):
    """Get the latest cashflow prediction for the user."""
    # Get latest prediction from database
    predictions = predictor.db.get_user_documents("cashflow_predictions", current_user["user_id"])
    
    if not predictions:
        # Generate new prediction if none exists
        prediction = await predictor.predict_cashflow(current_user["user_id"])
        return PredictionResponse(**prediction.to_firebase_dict())
    
    # Get most recent prediction
    latest_prediction = max(predictions, key=lambda x: x.get("prediction_date", ""))
    prediction_obj = CashflowPrediction.from_firebase_dict(latest_prediction)
    
    return PredictionResponse(**prediction_obj.to_firebase_dict())


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_current_user),
    predictor: CashflowPredictor = Depends(get_cashflow_predictor)
):
    """Get a specific prediction by ID."""
    prediction_data = predictor.db.get_document("cashflow_predictions", prediction_id)
    
    if not prediction_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    if prediction_data.get("user_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    prediction = CashflowPrediction.from_firebase_dict(prediction_data)
    return PredictionResponse(**prediction.to_firebase_dict())


@router.get("/", response_model=List[PredictionResponse])
async def get_predictions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    predictor: CashflowPredictor = Depends(get_cashflow_predictor)
):
    """Get user's prediction history."""
    predictions_data = predictor.db.get_user_documents("cashflow_predictions", current_user["user_id"])
    
    # Sort by prediction date (newest first) and limit
    predictions_data.sort(key=lambda x: x.get("prediction_date", ""), reverse=True)
    predictions_data = predictions_data[:limit]
    
    predictions = [CashflowPrediction.from_firebase_dict(p) for p in predictions_data]
    return [PredictionResponse(**p.to_firebase_dict()) for p in predictions]


@router.post("/validate/{prediction_id}", response_model=dict)
async def validate_prediction(
    prediction_id: str,
    actual_balance: float,
    current_user: dict = Depends(get_current_user),
    predictor: CashflowPredictor = Depends(get_cashflow_predictor)
):
    """Validate a prediction with actual results."""
    prediction_data = predictor.db.get_document("cashflow_predictions", prediction_id)
    
    if not prediction_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    if prediction_data.get("user_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    prediction = CashflowPrediction.from_firebase_dict(prediction_data)
    
    # Calculate accuracy
    predicted_balance = prediction.predicted_balance
    accuracy = 1.0 - abs(actual_balance - predicted_balance) / max(abs(predicted_balance), 1.0)
    
    # Update prediction with validation data
    update_data = {
        "is_validated": True,
        "actual_balance": actual_balance,
        "prediction_accuracy": accuracy,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    success = predictor.db.update_document("cashflow_predictions", prediction_id, update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to validate prediction"
        )
    
    return {
        "prediction_id": prediction_id,
        "predicted_balance": predicted_balance,
        "actual_balance": actual_balance,
        "accuracy": accuracy,
        "validated": True
    }


# Helper function (should be imported from main.py)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    return {"user_id": "user_123", "phone_number": "+1234567890"}


# Import dependencies
from datetime import datetime
from app.main import security
