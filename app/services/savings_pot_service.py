"""Savings pot service for managing savings goals and pots."""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math

from app.database import FirebaseDatabase
from app.models.firebase_models import SavingsPot, PotType, PotStatus


class SavingsPotService:
    """Service for savings pot-related operations."""
    
    def __init__(self, db: FirebaseDatabase):
        self.db = db
        self.collection_name = "savings_pots"
    
    async def create_pot(self, user_id: str, pot_data: Dict[str, Any]) -> SavingsPot:
        """Create a new savings pot."""
        pot_id = str(uuid.uuid4())
        
        # Parse target date if provided
        target_date = None
        if pot_data.get("target_date"):
            target_date = datetime.fromisoformat(pot_data["target_date"])
        
        # Create pot object
        pot = SavingsPot(
            pot_id=pot_id,
            user_id=user_id,
            name=pot_data["name"],
            description=pot_data.get("description"),
            pot_type=PotType(pot_data["pot_type"]),
            target_amount=pot_data.get("target_amount"),
            current_amount=0.0,
            currency="INR",
            target_date=target_date,
            monthly_contribution=pot_data.get("monthly_contribution"),
            contribution_frequency=pot_data.get("contribution_frequency", "monthly"),
            auto_contribute=pot_data.get("auto_contribute", False),
            status=PotStatus.ACTIVE,
            is_locked=pot_data.get("is_locked", False),
            is_emergency_accessible=pot_data.get("is_emergency_accessible", False),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Calculate suggested monthly contribution if not provided
        if not pot.monthly_contribution and pot.target_amount and pot.target_date:
            pot.monthly_contribution = self._calculate_suggested_contribution(
                pot.target_amount, pot.target_date
            )
        
        # Save to Firebase
        success = self.db.create_document(
            self.collection_name,
            pot_id,
            pot.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to create savings pot in database")
        
        return pot
    
    async def get_pot(self, pot_id: str) -> Optional[SavingsPot]:
        """Get savings pot by ID."""
        pot_data = self.db.get_document(self.collection_name, pot_id)
        if not pot_data:
            return None
        
        return SavingsPot.from_firebase_dict(pot_data)
    
    async def get_user_pots(self, user_id: str, pot_type: Optional[PotType] = None,
                           status: Optional[PotStatus] = None) -> List[SavingsPot]:
        """Get user's savings pots with optional filtering."""
        pots_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Apply filters
        filtered_pots = []
        for p_data in pots_data:
            # Check pot type filter
            if pot_type and p_data.get("pot_type") != pot_type.value:
                continue
            
            # Check status filter
            if status and p_data.get("status") != status.value:
                continue
            
            filtered_pots.append(SavingsPot.from_firebase_dict(p_data))
        
        # Sort by created_at (newest first)
        filtered_pots.sort(key=lambda x: x.created_at, reverse=True)
        
        return filtered_pots
    
    async def update_pot(self, pot_id: str, user_id: str, 
                        update_data: Dict[str, Any]) -> Optional[SavingsPot]:
        """Update savings pot information."""
        # Get existing pot
        pot = await self.get_pot(pot_id)
        if not pot or pot.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(pot, key):
                setattr(pot, key, value)
        
        # Recalculate progress if target amount changed
        if "target_amount" in update_data:
            pot.progress_percentage = pot.calculate_progress_percentage()
        
        pot.updated_at = datetime.utcnow()
        
        # Save to Firebase
        success = self.db.update_document(
            self.collection_name,
            pot_id,
            pot.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update savings pot in database")
        
        return pot
    
    async def delete_pot(self, pot_id: str, user_id: str) -> bool:
        """Delete savings pot (soft delete by changing status)."""
        pot = await self.get_pot(pot_id)
        if not pot or pot.user_id != user_id:
            return False
        
        # Soft delete by changing status to archived
        pot.status = PotStatus.ARCHIVED
        pot.updated_at = datetime.utcnow()
        
        success = self.db.update_document(
            self.collection_name,
            pot_id,
            pot.to_firebase_dict()
        )
        
        return success
    
    async def add_contribution(self, pot_id: str, user_id: str, 
                             amount: float, source: str = "manual") -> Dict[str, Any]:
        """Add a contribution to a savings pot."""
        pot = await self.get_pot(pot_id)
        if not pot or pot.user_id != user_id:
            raise Exception("Savings pot not found")
        
        if pot.status != PotStatus.ACTIVE:
            raise Exception("Cannot contribute to inactive pot")
        
        if pot.is_locked and pot.target_date and datetime.utcnow() < pot.target_date:
            raise Exception("Cannot contribute to locked pot before target date")
        
        # Add contribution
        pot.add_contribution(amount, source)
        
        # Save to database
        success = self.db.update_document(
            self.collection_name,
            pot_id,
            pot.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update savings pot")
        
        return {
            "pot_id": pot_id,
            "contribution_amount": amount,
            "new_balance": pot.current_amount,
            "progress_percentage": pot.progress_percentage,
            "is_fully_funded": pot.is_fully_funded,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def make_withdrawal(self, pot_id: str, user_id: str, 
                            amount: float, reason: str = None) -> Dict[str, Any]:
        """Make a withdrawal from a savings pot."""
        pot = await self.get_pot(pot_id)
        if not pot or pot.user_id != user_id:
            raise Exception("Savings pot not found")
        
        if pot.status != PotStatus.ACTIVE:
            raise Exception("Cannot withdraw from inactive pot")
        
        if pot.is_locked and pot.target_date and datetime.utcnow() < pot.target_date:
            if not pot.is_emergency_accessible:
                raise Exception("Cannot withdraw from locked pot")
            if not reason or "emergency" not in reason.lower():
                raise Exception("Locked pot requires emergency reason for withdrawal")
        
        if amount > pot.current_amount:
            raise Exception("Insufficient funds in pot")
        
        # Make withdrawal
        pot.make_withdrawal(amount, reason)
        
        # Save to database
        success = self.db.update_document(
            self.collection_name,
            pot_id,
            pot.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update savings pot")
        
        return {
            "pot_id": pot_id,
            "withdrawal_amount": amount,
            "new_balance": pot.current_amount,
            "progress_percentage": pot.progress_percentage,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_pot_progress(self, pot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information for a savings pot."""
        pot = await self.get_pot(pot_id)
        if not pot or pot.user_id != user_id:
            return None
        
        # Calculate additional progress metrics
        days_remaining = None
        if pot.target_date:
            days_remaining = max(0, (pot.target_date - datetime.utcnow()).days)
        
        projected_completion = None
        if pot.monthly_contribution and pot.monthly_contribution > 0:
            months_needed = math.ceil(pot.remaining_amount / pot.monthly_contribution)
            projected_completion = datetime.utcnow() + timedelta(days=months_needed * 30.44)
        
        return {
            "pot_id": pot_id,
            "name": pot.name,
            "pot_type": pot.pot_type.value,
            "current_amount": pot.current_amount,
            "target_amount": pot.target_amount,
            "remaining_amount": pot.remaining_amount,
            "progress_percentage": pot.progress_percentage,
            "is_fully_funded": pot.is_fully_funded,
            "target_date": pot.target_date.isoformat() if pot.target_date else None,
            "days_remaining": days_remaining,
            "monthly_contribution": pot.monthly_contribution,
            "projected_completion": projected_completion.isoformat() if projected_completion else None,
            "total_contributions": pot.total_contributions,
            "total_withdrawals": pot.total_withdrawals,
            "net_contributions": pot.total_contributions - pot.total_withdrawals,
            "status": pot.status.value,
            "is_locked": pot.is_locked,
            "is_emergency_accessible": pot.is_emergency_accessible
        }
    
    async def get_pots_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics summary for all user's savings pots."""
        pots = await self.get_user_pots(user_id)
        
        if not pots:
            return {
                "total_pots": 0,
                "total_savings": 0,
                "total_target": 0,
                "overall_progress": 0,
                "pot_types": {},
                "active_pots": 0,
                "completed_pots": 0,
                "insights": []
            }
        
        # Calculate metrics
        total_pots = len(pots)
        total_savings = sum(pot.current_amount for pot in pots)
        total_target = sum(pot.target_amount or 0 for pot in pots if pot.target_amount)
        overall_progress = (total_savings / max(total_target, 1)) * 100 if total_target > 0 else 0
        
        active_pots = len([p for p in pots if p.status == PotStatus.ACTIVE])
        completed_pots = len([p for p in pots if p.status == PotStatus.COMPLETED])
        
        # Pot type breakdown
        pot_types = {}
        for pot in pots:
            pot_type = pot.pot_type.value
            if pot_type not in pot_types:
                pot_types[pot_type] = {
                    "count": 0,
                    "total_amount": 0,
                    "average_progress": 0
                }
            pot_types[pot_type]["count"] += 1
            pot_types[pot_type]["total_amount"] += pot.current_amount
        
        # Calculate average progress for each type
        for pot_type, data in pot_types.items():
            type_pots = [p for p in pots if p.pot_type.value == pot_type]
            if type_pots:
                data["average_progress"] = sum(p.progress_percentage for p in type_pots) / len(type_pots)
        
        # Generate insights
        insights = self._generate_pot_insights(pots, total_savings, overall_progress)
        
        return {
            "total_pots": total_pots,
            "total_savings": total_savings,
            "total_target": total_target,
            "overall_progress": overall_progress,
            "pot_types": pot_types,
            "active_pots": active_pots,
            "completed_pots": completed_pots,
            "average_pot_size": total_savings / max(total_pots, 1),
            "insights": insights
        }
    
    def _calculate_suggested_contribution(self, target_amount: float, target_date: datetime) -> float:
        """Calculate suggested monthly contribution to reach target."""
        months_remaining = max(1, (target_date - datetime.utcnow()).days / 30.44)
        return target_amount / months_remaining
    
    def _generate_pot_insights(self, pots: List[SavingsPot], total_savings: float, 
                              overall_progress: float) -> List[str]:
        """Generate insights from savings pots data."""
        insights = []
        
        if overall_progress > 80:
            insights.append("Excellent progress! You're close to achieving your savings goals.")
        elif overall_progress > 50:
            insights.append("Good progress on your savings goals. Keep up the momentum!")
        elif overall_progress > 20:
            insights.append("You've made a good start on savings. Consider increasing contributions.")
        else:
            insights.append("Consider setting up automatic contributions to boost your savings.")
        
        # Check for completed pots
        completed_pots = [p for p in pots if p.status == PotStatus.COMPLETED]
        if completed_pots:
            insights.append(f"Congratulations! You've completed {len(completed_pots)} savings goal(s).")
        
        # Check for emergency fund
        emergency_pots = [p for p in pots if p.pot_type == PotType.EMERGENCY]
        if not emergency_pots:
            insights.append("Consider creating an emergency fund for unexpected expenses.")
        else:
            emergency_total = sum(p.current_amount for p in emergency_pots)
            if emergency_total < 10000:  # Configurable threshold
                insights.append("Your emergency fund could be larger. Aim for 3-6 months of expenses.")
        
        # Check for diversified savings
        if len(pots) > 1:
            insights.append("Great job diversifying your savings across multiple goals!")
        
        return insights
