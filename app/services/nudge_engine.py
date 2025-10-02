"""Nudge engine service for generating and managing financial nudges."""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.database import FirebaseDatabase
from app.models.firebase_models import Nudge, NudgeType, NudgePriority, NudgeStatus, CashflowPrediction
from app.services.cashflow_predictor import CashflowPredictor


class NudgeEngine:
    """Service for generating and managing financial nudges."""
    
    def __init__(self):
        self.db = FirebaseDatabase()
        self.collection_name = "nudges"
        self.cashflow_predictor = CashflowPredictor()
    
    async def generate_user_nudges(self, user_id: str) -> Dict[str, Any]:
        """Generate nudges for a user based on their current financial situation."""
        # Get latest cashflow prediction
        predictions = self.db.get_user_documents("cashflow_predictions", user_id)
        
        if not predictions:
            # Generate new prediction first
            prediction = await self.cashflow_predictor.predict_cashflow(user_id)
        else:
            # Use latest prediction
            latest_prediction = max(predictions, key=lambda x: x.get("prediction_date", ""))
            prediction = CashflowPrediction.from_firebase_dict(latest_prediction)
        
        # Generate nudges based on prediction
        nudges = []
        
        # Shortfall risk nudge
        if prediction.shortfall_probability > 0.7:
            nudge = await self._create_shortfall_nudge(user_id, prediction)
            nudges.append(nudge)
        
        # Low balance alert
        if prediction.predicted_balance < 1000:  # Configurable threshold
            nudge = await self._create_low_balance_nudge(user_id, prediction)
            nudges.append(nudge)
        
        # Savings opportunity nudge
        if prediction.predicted_balance > 2000 and prediction.shortfall_probability < 0.3:
            nudge = await self._create_savings_nudge(user_id, prediction)
            nudges.append(nudge)
        
        # Spending pattern nudge
        spending_nudge = await self._create_spending_pattern_nudge(user_id)
        if spending_nudge:
            nudges.append(spending_nudge)
        
        return {
            "generated_count": len(nudges),
            "nudge_ids": [n.nudge_id for n in nudges],
            "prediction_id": prediction.prediction_id
        }
    
    async def _create_shortfall_nudge(self, user_id: str, prediction: CashflowPrediction) -> Nudge:
        """Create a nudge for predicted shortfall."""
        shortfall_amount = prediction.shortfall_amount or 0
        days_until_shortfall = prediction.days_until_shortfall or 3
        
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="Potential Cash Flow Issue",
            message=f"We predict you might face a shortfall of ₹{shortfall_amount:.0f} in {days_until_shortfall} days. Consider moving some money to your emergency fund or reducing discretionary spending.",
            nudge_type=NudgeType.ACTIONABLE,
            priority=NudgePriority.HIGH,
            suggested_action={
                "type": "save_to_emergency",
                "amount": min(shortfall_amount * 0.5, 500),
                "description": "Save to emergency fund"
            },
            action_amount=min(shortfall_amount * 0.5, 500),
            scheduled_for=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            trigger_event="shortfall_prediction",
            cashflow_prediction_id=prediction.prediction_id,
            reasoning=prediction.prediction_reasoning,
            confidence_score=prediction.confidence_level,
            delivery_channels=["in_app", "sms"],
            preferred_channel="in_app"
        )
        
        # Save to database
        self.db.create_document(self.collection_name, nudge.nudge_id, nudge.to_firebase_dict())
        return nudge
    
    async def _create_low_balance_nudge(self, user_id: str, prediction: CashflowPrediction) -> Nudge:
        """Create a nudge for low balance."""
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="Low Balance Alert",
            message=f"Your predicted balance is ₹{prediction.predicted_balance:.0f}. Consider being extra careful with spending and avoid any non-essential purchases.",
            nudge_type=NudgeType.INFORMATIONAL,
            priority=NudgePriority.MEDIUM,
            scheduled_for=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=12),
            trigger_event="low_balance",
            cashflow_prediction_id=prediction.prediction_id,
            reasoning="Current cash flow forecast indicates low balance",
            confidence_score=prediction.confidence_level,
            delivery_channels=["in_app"],
            preferred_channel="in_app"
        )
        
        self.db.create_document(self.collection_name, nudge.nudge_id, nudge.to_firebase_dict())
        return nudge
    
    async def _create_savings_nudge(self, user_id: str, prediction: CashflowPrediction) -> Nudge:
        """Create a nudge for savings opportunity."""
        savings_amount = min(prediction.predicted_balance * 0.1, 1000)  # 10% or max 1000
        
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="Great Savings Opportunity!",
            message=f"Your cash flow looks healthy with a predicted balance of ₹{prediction.predicted_balance:.0f}. Consider saving ₹{savings_amount:.0f} to build your emergency fund or work towards your goals.",
            nudge_type=NudgeType.ACTIONABLE,
            priority=NudgePriority.LOW,
            suggested_action={
                "type": "save_to_emergency",
                "amount": savings_amount,
                "description": "Save to emergency fund"
            },
            action_amount=savings_amount,
            scheduled_for=datetime.utcnow() + timedelta(hours=2),  # Delay to not be too pushy
            expires_at=datetime.utcnow() + timedelta(days=3),
            trigger_event="savings_opportunity",
            cashflow_prediction_id=prediction.prediction_id,
            reasoning="Healthy cash flow provides opportunity for savings",
            confidence_score=prediction.confidence_level,
            delivery_channels=["in_app"],
            preferred_channel="in_app"
        )
        
        self.db.create_document(self.collection_name, nudge.nudge_id, nudge.to_firebase_dict())
        return nudge
    
    async def _create_spending_pattern_nudge(self, user_id: str) -> Optional[Nudge]:
        """Create a nudge based on spending patterns."""
        # Get recent transactions
        transactions = self.db.get_user_documents("transactions", user_id)
        
        if not transactions:
            return None
        
        # Analyze spending patterns (simplified)
        recent_transactions = [
            t for t in transactions 
            if datetime.fromisoformat(t["transaction_date"]) > datetime.utcnow() - timedelta(days=7)
        ]
        
        if not recent_transactions:
            return None
        
        # Check for high discretionary spending
        discretionary_categories = ["entertainment", "dining", "shopping"]
        discretionary_total = sum(
            t["amount"] for t in recent_transactions 
            if t.get("category") in discretionary_categories
        )
        
        if discretionary_total > 2000:  # Configurable threshold
            nudge = Nudge(
                nudge_id=str(uuid.uuid4()),
                user_id=user_id,
                title="High Discretionary Spending",
                message=f"You've spent ₹{discretionary_total:.0f} on discretionary items this week. Consider reducing this by 20% to improve your savings.",
                nudge_type=NudgeType.INFORMATIONAL,
                priority=NudgePriority.MEDIUM,
                scheduled_for=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                trigger_event="high_discretionary_spending",
                reasoning=f"Spent ₹{discretionary_total:.0f} on discretionary items in the last 7 days",
                confidence_score=0.8,
                delivery_channels=["in_app"],
                preferred_channel="in_app"
            )
            
            self.db.create_document(self.collection_name, nudge.nudge_id, nudge.to_firebase_dict())
            return nudge
        
        return None
    
    async def get_user_nudges(self, user_id: str, status_filter: Optional[NudgeStatus] = None, 
                            limit: int = 20) -> List[Nudge]:
        """Get user's nudges with optional filtering."""
        nudges_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Apply status filter
        if status_filter:
            nudges_data = [n for n in nudges_data if n.get("status") == status_filter.value]
        
        # Sort by scheduled_for (newest first) and limit
        nudges_data.sort(key=lambda x: x.get("scheduled_for", ""), reverse=True)
        nudges_data = nudges_data[:limit]
        
        return [Nudge.from_firebase_dict(n) for n in nudges_data]
    
    async def get_pending_nudges(self, user_id: str) -> List[Nudge]:
        """Get nudges that are ready to be delivered."""
        nudges_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Filter for pending nudges that are deliverable
        pending_nudges = []
        for n_data in nudges_data:
            if n_data.get("status") == NudgeStatus.PENDING.value:
                nudge = Nudge.from_firebase_dict(n_data)
                if nudge.is_deliverable:
                    pending_nudges.append(nudge)
        
        # Sort by priority and scheduled time
        pending_nudges.sort(key=lambda x: (x.priority.value, x.scheduled_for))
        
        return pending_nudges
    
    async def get_nudge(self, nudge_id: str) -> Optional[Nudge]:
        """Get nudge by ID."""
        nudge_data = self.db.get_document(self.collection_name, nudge_id)
        if not nudge_data:
            return None
        
        return Nudge.from_firebase_dict(nudge_data)
    
    async def update_nudge(self, nudge_id: str, user_id: str, 
                          update_data: Dict[str, Any]) -> Optional[Nudge]:
        """Update nudge with user response or status change."""
        nudge = await self.get_nudge(nudge_id)
        if not nudge or nudge.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(nudge, key):
                setattr(nudge, key, value)
        
        nudge.updated_at = datetime.utcnow()
        
        # Save to database
        success = self.db.update_document(
            self.collection_name,
            nudge_id,
            nudge.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update nudge in database")
        
        return nudge
    
    async def deliver_nudge(self, nudge_id: str, user_id: str, channel: str) -> Dict[str, Any]:
        """Deliver a nudge through specified channel."""
        nudge = await self.get_nudge(nudge_id)
        if not nudge or nudge.user_id != user_id:
            raise Exception("Nudge not found")
        
        if not nudge.is_deliverable:
            raise Exception("Nudge is not deliverable")
        
        # Update nudge status
        nudge.status = NudgeStatus.DELIVERED
        nudge.delivered_at = datetime.utcnow()
        
        # Save to database
        self.db.update_document(
            self.collection_name,
            nudge_id,
            nudge.to_firebase_dict()
        )
        
        # TODO: Implement actual delivery through channel (SMS, push notification, etc.)
        
        return {
            "nudge_id": nudge_id,
            "delivered": True,
            "channel": channel,
            "delivered_at": nudge.delivered_at.isoformat()
        }
    
    async def user_act_on_nudge(self, nudge_id: str, user_id: str, 
                               action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's action on a nudge."""
        nudge = await self.get_nudge(nudge_id)
        if not nudge or nudge.user_id != user_id:
            raise Exception("Nudge not found")
        
        # Update nudge with user response
        nudge.status = NudgeStatus.ACTED_UPON
        nudge.user_response = action_data
        nudge.action_taken = True
        nudge.action_result = {
            "action_type": action_data.get("action_type"),
            "amount": action_data.get("amount"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save to database
        self.db.update_document(
            self.collection_name,
            nudge_id,
            nudge.to_firebase_dict()
        )
        
        # TODO: Execute the actual action (transfer money, create savings pot, etc.)
        
        return {
            "nudge_id": nudge_id,
            "action_taken": True,
            "action_result": nudge.action_result
        }
    
    async def get_nudge_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get nudge effectiveness analytics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        nudges_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Filter by date
        recent_nudges = [
            n for n in nudges_data 
            if datetime.fromisoformat(n.get("created_at", "")) >= cutoff_date
        ]
        
        if not recent_nudges:
            return {
                "period_days": days,
                "total_nudges": 0,
                "delivered_nudges": 0,
                "acted_upon_nudges": 0,
                "effectiveness_rate": 0,
                "average_satisfaction": 0,
                "nudge_types": {},
                "insights": []
            }
        
        # Calculate metrics
        total_nudges = len(recent_nudges)
        delivered_nudges = len([n for n in recent_nudges if n.get("status") in ["delivered", "acknowledged", "acted_upon"]])
        acted_upon_nudges = len([n for n in recent_nudges if n.get("status") == "acted_upon"])
        
        effectiveness_rate = (acted_upon_nudges / max(delivered_nudges, 1)) * 100
        
        # Calculate average satisfaction
        satisfaction_scores = [n.get("user_satisfaction") for n in recent_nudges if n.get("user_satisfaction")]
        average_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        
        # Nudge type breakdown
        nudge_types = {}
        for nudge in recent_nudges:
            nudge_type = nudge.get("nudge_type", "unknown")
            if nudge_type not in nudge_types:
                nudge_types[nudge_type] = {"total": 0, "acted_upon": 0}
            nudge_types[nudge_type]["total"] += 1
            if nudge.get("status") == "acted_upon":
                nudge_types[nudge_type]["acted_upon"] += 1
        
        # Generate insights
        insights = self._generate_analytics_insights(
            total_nudges, delivered_nudges, acted_upon_nudges, 
            effectiveness_rate, average_satisfaction
        )
        
        return {
            "period_days": days,
            "total_nudges": total_nudges,
            "delivered_nudges": delivered_nudges,
            "acted_upon_nudges": acted_upon_nudges,
            "effectiveness_rate": effectiveness_rate,
            "average_satisfaction": average_satisfaction,
            "nudge_types": nudge_types,
            "insights": insights
        }
    
    def _generate_analytics_insights(self, total_nudges: int, delivered_nudges: int, 
                                   acted_upon_nudges: int, effectiveness_rate: float, 
                                   average_satisfaction: float) -> List[str]:
        """Generate insights from nudge analytics."""
        insights = []
        
        if effectiveness_rate > 60:
            insights.append("Great job! You're acting on most of the financial suggestions.")
        elif effectiveness_rate > 30:
            insights.append("You're responding well to some suggestions. Consider being more proactive with financial actions.")
        else:
            insights.append("Try to act on more financial suggestions to improve your financial health.")
        
        if average_satisfaction > 4:
            insights.append("The financial suggestions are well-received. Keep up the good work!")
        elif average_satisfaction < 3:
            insights.append("Consider providing feedback to help improve the relevance of suggestions.")
        
        if delivered_nudges < total_nudges * 0.8:
            insights.append("Many nudges aren't being delivered. Check your notification settings.")
        
        return insights
