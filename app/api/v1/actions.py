"""Autonomous action management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import AutonomousAction, ActionType, ActionStatus, ActionRiskLevel
from app.services.decision_engine import DecisionEngine

router = APIRouter()


class ActionResponse(BaseModel):
    """Action response model."""
    action_id: str
    user_id: str
    action_type: str
    action_name: str
    description: str
    amount: Optional[float]
    source_account: Optional[str]
    destination_account: Optional[str]
    risk_level: str
    status: str
    trigger_reason: str
    scheduled_for: Optional[str]
    executed_at: Optional[str]
    requires_confirmation: bool
    user_confirmed: bool
    can_be_reversed: bool
    execution_result: Optional[dict]


class ActionCreate(BaseModel):
    """Action creation request model."""
    action_type: ActionType
    amount: Optional[float] = None
    source_account: Optional[str] = None
    destination_account: Optional[str] = None
    action_parameters: dict = {}


class ActionUpdate(BaseModel):
    """Action update request model."""
    status: Optional[ActionStatus] = None
    user_confirmed: Optional[bool] = None
    user_feedback: Optional[dict] = None


def get_decision_engine() -> DecisionEngine:
    """Get decision engine instance."""
    return DecisionEngine()


@router.get("/", response_model=List[ActionResponse])
async def get_actions(
    status_filter: Optional[ActionStatus] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Get user's autonomous actions with optional status filtering."""
    actions = await decision_engine.get_user_actions(
        current_user["user_id"],
        status_filter=status_filter,
        limit=limit
    )
    return [ActionResponse(**a.to_firebase_dict()) for a in actions]


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: str,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Get a specific action by ID."""
    action = await decision_engine.get_action(action_id)
    
    if not action or action.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found"
        )
    
    return ActionResponse(**action.to_firebase_dict())


@router.post("/", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    action_data: ActionCreate,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Create a new autonomous action."""
    try:
        action = await decision_engine.create_action(
            current_user["user_id"],
            action_data.dict()
        )
        return ActionResponse(**action.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create action: {str(e)}"
        )


@router.put("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: str,
    action_update: ActionUpdate,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Update action status or user response."""
    try:
        action = await decision_engine.update_action(
            action_id,
            current_user["user_id"],
            action_update.dict(exclude_unset=True)
        )
        
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action not found"
            )
        
        return ActionResponse(**action.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update action: {str(e)}"
        )


@router.post("/{action_id}/execute", response_model=dict)
async def execute_action(
    action_id: str,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Execute a pending action."""
    try:
        result = await decision_engine.execute_action(
            action_id,
            current_user["user_id"]
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute action: {str(e)}"
        )


@router.post("/{action_id}/confirm", response_model=dict)
async def confirm_action(
    action_id: str,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Confirm a pending action."""
    try:
        result = await decision_engine.confirm_action(
            action_id,
            current_user["user_id"]
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to confirm action: {str(e)}"
        )


@router.post("/{action_id}/reverse", response_model=dict)
async def reverse_action(
    action_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Reverse a completed action."""
    try:
        result = await decision_engine.reverse_action(
            action_id,
            current_user["user_id"],
            reason
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reverse action: {str(e)}"
        )


@router.post("/suggest", response_model=dict)
async def suggest_actions(
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Get suggested actions for the user based on their current situation."""
    try:
        suggestions = await decision_engine.suggest_actions(current_user["user_id"])
        return suggestions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/analytics/effectiveness", response_model=dict)
async def get_action_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    decision_engine: DecisionEngine = Depends(get_decision_engine)
):
    """Get action effectiveness analytics."""
    analytics = await decision_engine.get_action_analytics(
        current_user["user_id"],
        days=days
    )
    return analytics


# Helper function (should be imported from main.py)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    return {"user_id": "user_123", "phone_number": "+1234567890"}


# Import dependencies
from app.main import security
