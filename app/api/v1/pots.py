"""Savings pots management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import SavingsPot, PotType, PotStatus
from app.services.savings_pot_service import SavingsPotService

router = APIRouter()


class PotCreate(BaseModel):
    """Savings pot creation request model."""
    name: str
    description: Optional[str] = None
    pot_type: PotType
    target_amount: Optional[float] = None
    target_date: Optional[str] = None  # ISO format
    monthly_contribution: Optional[float] = None
    contribution_frequency: str = "monthly"
    auto_contribute: bool = False
    is_locked: bool = False
    is_emergency_accessible: bool = False


class PotUpdate(BaseModel):
    """Savings pot update request model."""
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[str] = None
    monthly_contribution: Optional[float] = None
    contribution_frequency: Optional[str] = None
    auto_contribute: Optional[bool] = None
    is_locked: Optional[bool] = None
    is_emergency_accessible: Optional[bool] = None
    status: Optional[PotStatus] = None


class PotResponse(BaseModel):
    """Savings pot response model."""
    pot_id: str
    user_id: str
    name: str
    description: Optional[str]
    pot_type: str
    target_amount: Optional[float]
    current_amount: float
    currency: str
    target_date: Optional[str]
    status: str
    is_locked: bool
    is_emergency_accessible: bool
    monthly_contribution: Optional[float]
    contribution_frequency: str
    auto_contribute: bool
    progress_percentage: float
    total_contributions: float
    total_withdrawals: float
    created_at: str


class ContributionRequest(BaseModel):
    """Contribution request model."""
    amount: float
    source: str = "manual"


class WithdrawalRequest(BaseModel):
    """Withdrawal request model."""
    amount: float
    reason: Optional[str] = None


def get_savings_pot_service(db: FirebaseDatabase = Depends(get_database)) -> SavingsPotService:
    """Get savings pot service instance."""
    return SavingsPotService(db)


@router.post("/", response_model=PotResponse, status_code=status.HTTP_201_CREATED)
async def create_pot(
    pot_data: PotCreate,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Create a new savings pot."""
    try:
        pot = await pot_service.create_pot(
            current_user["user_id"],
            pot_data.dict()
        )
        return PotResponse(**pot.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create savings pot: {str(e)}"
        )


@router.get("/", response_model=List[PotResponse])
async def get_pots(
    pot_type: Optional[PotType] = None,
    status: Optional[PotStatus] = None,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Get user's savings pots with optional filtering."""
    pots = await pot_service.get_user_pots(
        current_user["user_id"],
        pot_type=pot_type,
        status=status
    )
    return [PotResponse(**p.to_firebase_dict()) for p in pots]


@router.get("/{pot_id}", response_model=PotResponse)
async def get_pot(
    pot_id: str,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Get a specific savings pot by ID."""
    pot = await pot_service.get_pot(pot_id)
    
    if not pot or pot.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings pot not found"
        )
    
    return PotResponse(**pot.to_firebase_dict())


@router.put("/{pot_id}", response_model=PotResponse)
async def update_pot(
    pot_id: str,
    pot_update: PotUpdate,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Update a savings pot."""
    try:
        pot = await pot_service.update_pot(
            pot_id,
            current_user["user_id"],
            pot_update.dict(exclude_unset=True)
        )
        
        if not pot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Savings pot not found"
            )
        
        return PotResponse(**pot.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update savings pot: {str(e)}"
        )


@router.delete("/{pot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pot(
    pot_id: str,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Delete a savings pot (soft delete)."""
    success = await pot_service.delete_pot(pot_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings pot not found"
        )


@router.post("/{pot_id}/contribute", response_model=dict)
async def contribute_to_pot(
    pot_id: str,
    contribution: ContributionRequest,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Add a contribution to a savings pot."""
    try:
        result = await pot_service.add_contribution(
            pot_id,
            current_user["user_id"],
            contribution.amount,
            contribution.source
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add contribution: {str(e)}"
        )


@router.post("/{pot_id}/withdraw", response_model=dict)
async def withdraw_from_pot(
    pot_id: str,
    withdrawal: WithdrawalRequest,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Make a withdrawal from a savings pot."""
    try:
        result = await pot_service.make_withdrawal(
            pot_id,
            current_user["user_id"],
            withdrawal.amount,
            withdrawal.reason
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to make withdrawal: {str(e)}"
        )


@router.get("/{pot_id}/progress", response_model=dict)
async def get_pot_progress(
    pot_id: str,
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Get progress details for a savings pot."""
    progress = await pot_service.get_pot_progress(pot_id, current_user["user_id"])
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings pot not found"
        )
    return progress


@router.get("/analytics/summary", response_model=dict)
async def get_pots_analytics(
    current_user: dict = Depends(get_current_user),
    pot_service: SavingsPotService = Depends(get_savings_pot_service)
):
    """Get analytics summary for all savings pots."""
    analytics = await pot_service.get_pots_analytics(current_user["user_id"])
    return analytics


# Helper function (should be imported from main.py)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    return {"user_id": "user_123", "phone_number": "+1234567890"}


# Import dependencies
from app.main import security
