"""User service for managing user operations."""
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from app.database import FirebaseDatabase
from app.models.firebase_models import User


class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db: FirebaseDatabase):
        self.db = db
        self.collection_name = "users"
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        
        # Create user object
        user = User(
            user_id=user_id,
            phone_number=user_data["phone_number"],
            email=user_data.get("email"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            preferred_language=user_data.get("preferred_language", "en"),
            timezone=user_data.get("timezone", "UTC"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to Firebase
        success = self.db.create_document(
            self.collection_name,
            user_id,
            user.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to create user in database")
        
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        user_data = self.db.get_document(self.collection_name, user_id)
        if not user_data:
            return None
        
        return User.from_firebase_dict(user_data)
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user information."""
        # Get existing user
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        # Save to Firebase
        success = self.db.update_document(
            self.collection_name,
            user_id,
            user.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update user in database")
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # Soft delete by setting is_active to False
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        success = self.db.update_document(
            self.collection_name,
            user_id,
            user.to_firebase_dict()
        )
        
        return success
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's financial profile and insights."""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Get user's transactions for insights
        transactions = self.db.get_user_documents("transactions", user_id)
        
        # Calculate basic insights
        total_income = sum(
            t.get("amount", 0) for t in transactions 
            if t.get("transaction_type") == "income"
        )
        
        total_expenses = sum(
            t.get("amount", 0) for t in transactions 
            if t.get("transaction_type") == "expense"
        )
        
        net_worth = total_income - total_expenses
        
        # Get savings pots
        savings_pots = self.db.get_user_documents("savings_pots", user_id)
        total_savings = sum(pot.get("current_amount", 0) for pot in savings_pots)
        
        return {
            "user_id": user_id,
            "basic_info": {
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.phone_number,
                "phone": user.phone_number,
                "email": user.email,
                "income_schedule": user.income_schedule,
                "risk_tolerance": user.risk_tolerance
            },
            "financial_summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_worth": net_worth,
                "total_savings": total_savings,
                "monthly_commitments": user.monthly_commitments,
                "emergency_fund_target": user.emergency_fund_target
            },
            "savings_pots": savings_pots,
            "goals": {
                "short_term": user.short_term_goals,
                "long_term": user.long_term_goals
            },
            "preferences": {
                "auto_actions_enabled": user.auto_actions_enabled,
                "max_auto_action_amount": user.max_auto_action_amount,
                "preferred_language": user.preferred_language
            }
        }
    
    async def complete_onboarding(self, user_id: str, onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete user onboarding with financial information."""
        user = await self.get_user(user_id)
        if not user:
            raise Exception("User not found")
        
        # Update user with onboarding data
        update_fields = {}
        
        if "income_schedule" in onboarding_data:
            update_fields["income_schedule"] = onboarding_data["income_schedule"]
        
        if "typical_income_amount" in onboarding_data:
            update_fields["typical_income_amount"] = onboarding_data["typical_income_amount"]
        
        if "monthly_commitments" in onboarding_data:
            update_fields["monthly_commitments"] = onboarding_data["monthly_commitments"]
        
        if "emergency_fund_target" in onboarding_data:
            update_fields["emergency_fund_target"] = onboarding_data["emergency_fund_target"]
        
        if "risk_tolerance" in onboarding_data:
            update_fields["risk_tolerance"] = onboarding_data["risk_tolerance"]
        
        if "short_term_goals" in onboarding_data:
            update_fields["short_term_goals"] = onboarding_data["short_term_goals"]
        
        if "long_term_goals" in onboarding_data:
            update_fields["long_term_goals"] = onboarding_data["long_term_goals"]
        
        if "auto_actions_enabled" in onboarding_data:
            update_fields["auto_actions_enabled"] = onboarding_data["auto_actions_enabled"]
        
        if "max_auto_action_amount" in onboarding_data:
            update_fields["max_auto_action_amount"] = onboarding_data["max_auto_action_amount"]
        
        # Update user
        updated_user = await self.update_user(user_id, update_fields)
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "user_id": user_id,
            "next_steps": [
                "Connect your bank account or add transactions manually",
                "Set up your first savings pot",
                "Enable notifications for financial nudges"
            ]
        }
