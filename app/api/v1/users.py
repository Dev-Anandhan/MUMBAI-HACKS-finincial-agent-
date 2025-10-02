"""User management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import User
from app.services.user_service import UserService

router = APIRouter()


class UserCreate(BaseModel):
    """User creation request model."""
    phone_number: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    """User update request model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    income_schedule: Optional[str] = None
    typical_income_amount: Optional[float] = None
    monthly_commitments: Optional[float] = None
    emergency_fund_target: Optional[float] = None
    risk_tolerance: Optional[str] = None
    auto_actions_enabled: Optional[bool] = None
    max_auto_action_amount: Optional[float] = None


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    phone_number: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_language: str
    timezone: str
    income_schedule: Optional[str]
    typical_income_amount: Optional[float]
    income_variability: float
    monthly_commitments: float
    emergency_fund_target: float
    risk_tolerance: str
    auto_actions_enabled: bool
    max_auto_action_amount: float
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str


def get_user_service(db: FirebaseDatabase = Depends(get_database)) -> UserService:
    """Get user service instance."""
    return UserService(db)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    try:
        user = await user_service.create_user(user_data.dict())
        return UserResponse(**user.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(**user.to_firebase_dict())


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user information."""
    try:
        user = await user_service.update_user(user_id, user_update.dict(exclude_unset=True))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (soft delete)."""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/{user_id}/profile", response_model=dict)
async def get_user_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user's financial profile and insights."""
    profile = await user_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile


@router.post("/{user_id}/onboarding", response_model=dict)
async def complete_onboarding(
    user_id: str,
    onboarding_data: dict,
    user_service: UserService = Depends(get_user_service)
):
    """Complete user onboarding with financial information."""
    try:
        result = await user_service.complete_onboarding(user_id, onboarding_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete onboarding: {str(e)}"
        )
