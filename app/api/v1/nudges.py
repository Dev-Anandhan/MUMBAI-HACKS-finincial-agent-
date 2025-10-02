"""Nudge management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import Nudge, NudgeType, NudgePriority, NudgeStatus
from app.services.nudge_engine import NudgeEngine

router = APIRouter()


class NudgeResponse(BaseModel):
    """Nudge response model."""
    nudge_id: str
    user_id: str
    title: str
    message: str
    nudge_type: str
    priority: str
    status: str
    scheduled_for: str
    expires_at: Optional[str]
    delivered_at: Optional[str]
    suggested_action: Optional[dict]
    action_amount: Optional[float]
    confidence_score: float
    reasoning: Optional[str]
    is_expired: bool
    is_deliverable: bool


class NudgeUpdate(BaseModel):
    """Nudge update request model."""
    status: Optional[NudgeStatus] = None
    user_response: Optional[dict] = None
    action_taken: Optional[bool] = None
    user_satisfaction: Optional[int] = None


def get_nudge_engine() -> NudgeEngine:
    """Get nudge engine instance."""
    return NudgeEngine()


@router.get("/", response_model=List[NudgeResponse])
async def get_nudges(
    status_filter: Optional[NudgeStatus] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Get user's nudges with optional status filtering."""
    nudges = await nudge_engine.get_user_nudges(
        current_user["user_id"],
        status_filter=status_filter,
        limit=limit
    )
    return [NudgeResponse(**n.to_firebase_dict()) for n in nudges]


@router.get("/pending", response_model=List[NudgeResponse])
async def get_pending_nudges(
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Get pending nudges that can be delivered."""
    nudges = await nudge_engine.get_pending_nudges(current_user["user_id"])
    return [NudgeResponse(**n.to_firebase_dict()) for n in nudges]


@router.get("/{nudge_id}", response_model=NudgeResponse)
async def get_nudge(
    nudge_id: str,
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Get a specific nudge by ID."""
    nudge = await nudge_engine.get_nudge(nudge_id)
    
    if not nudge or nudge.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nudge not found"
        )
    
    return NudgeResponse(**nudge.to_firebase_dict())


@router.put("/{nudge_id}", response_model=NudgeResponse)
async def update_nudge(
    nudge_id: str,
    nudge_update: NudgeUpdate,
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Update nudge status or user response."""
    try:
        nudge = await nudge_engine.update_nudge(
            nudge_id,
            current_user["user_id"],
            nudge_update.dict(exclude_unset=True)
        )
        
        if not nudge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nudge not found"
            )
        
        return NudgeResponse(**nudge.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update nudge: {str(e)}"
        )


@router.post("/{nudge_id}/deliver", response_model=dict)
async def deliver_nudge(
    nudge_id: str,
    channel: str = "in_app",
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Deliver a nudge through specified channel."""
    try:
        result = await nudge_engine.deliver_nudge(
            nudge_id,
            current_user["user_id"],
            channel
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deliver nudge: {str(e)}"
        )


@router.post("/{nudge_id}/act", response_model=dict)
async def act_on_nudge(
    nudge_id: str,
    action_data: dict,
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """User acts on a nudge suggestion."""
    try:
        result = await nudge_engine.user_act_on_nudge(
            nudge_id,
            current_user["user_id"],
            action_data
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process nudge action: {str(e)}"
        )


@router.post("/generate", response_model=dict)
async def generate_nudges(
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Generate new nudges for the user based on their current situation."""
    try:
        result = await nudge_engine.generate_user_nudges(current_user["user_id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate nudges: {str(e)}"
        )


@router.get("/analytics/effectiveness", response_model=dict)
async def get_nudge_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    nudge_engine: NudgeEngine = Depends(get_nudge_engine)
):
    """Get nudge effectiveness analytics."""
    analytics = await nudge_engine.get_nudge_analytics(
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
