"""Transaction management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_database, FirebaseDatabase
from app.models.firebase_models import Transaction, TransactionType, TransactionCategory
from app.services.transaction_service import TransactionService

router = APIRouter()


class TransactionCreate(BaseModel):
    """Transaction creation request model."""
    amount: float
    currency: str = "INR"
    transaction_type: TransactionType
    category: Optional[TransactionCategory] = TransactionCategory.UNKNOWN
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    transaction_date: str  # ISO format
    source_account: Optional[str] = None
    source_type: Optional[str] = None
    location: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Transaction update request model."""
    category: Optional[TransactionCategory] = None
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    is_essential: Optional[bool] = None
    is_recurring: Optional[bool] = None


class TransactionResponse(BaseModel):
    """Transaction response model."""
    transaction_id: str
    amount: float
    currency: str
    transaction_type: str
    category: str
    description: Optional[str]
    merchant_name: Optional[str]
    transaction_date: str
    is_essential: Optional[bool]
    is_recurring: bool
    confidence_score: float
    created_at: str


def get_transaction_service(db: FirebaseDatabase = Depends(get_database)) -> TransactionService:
    """Get transaction service instance."""
    return TransactionService(db)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction."""
    try:
        transaction = await transaction_service.create_transaction(
            current_user["user_id"], 
            transaction_data.dict()
        )
        return TransactionResponse(**transaction.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[TransactionType] = None,
    category: Optional[TransactionCategory] = None,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Get user's transactions with optional filtering."""
    transactions = await transaction_service.get_user_transactions(
        current_user["user_id"],
        limit=limit,
        offset=offset,
        transaction_type=transaction_type,
        category=category
    )
    return [TransactionResponse(**t.to_firebase_dict()) for t in transactions]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Get a specific transaction."""
    transaction = await transaction_service.get_transaction(transaction_id)
    if not transaction or transaction.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return TransactionResponse(**transaction.to_firebase_dict())


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_update: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Update a transaction."""
    try:
        transaction = await transaction_service.update_transaction(
            transaction_id,
            current_user["user_id"],
            transaction_update.dict(exclude_unset=True)
        )
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        return TransactionResponse(**transaction.to_firebase_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update transaction: {str(e)}"
        )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Delete a transaction."""
    success = await transaction_service.delete_transaction(transaction_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )


@router.post("/bulk", response_model=dict)
async def create_bulk_transactions(
    transactions_data: List[TransactionCreate],
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Create multiple transactions at once."""
    try:
        result = await transaction_service.create_bulk_transactions(
            current_user["user_id"],
            [t.dict() for t in transactions_data]
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create bulk transactions: {str(e)}"
        )


@router.get("/analytics/summary", response_model=dict)
async def get_transaction_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction analytics and insights."""
    analytics = await transaction_service.get_transaction_analytics(
        current_user["user_id"],
        days=days
    )
    return analytics


@router.post("/classify", response_model=dict)
async def classify_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Manually classify a transaction."""
    try:
        result = await transaction_service.classify_transaction(
            transaction_id,
            current_user["user_id"]
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to classify transaction: {str(e)}"
        )


# Helper function (should be imported from main.py)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    return {"user_id": "user_123", "phone_number": "+1234567890"}


# Import security dependency
from app.main import security
