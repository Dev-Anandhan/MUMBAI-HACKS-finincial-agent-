"""Decision engine service for autonomous financial actions."""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.database import FirebaseDatabase
from app.models.firebase_models import (
    AutonomousAction, ActionType, ActionStatus, ActionRiskLevel,
    User, CashflowPrediction, Nudge
)
from app.config import settings


class DecisionEngine:
    """Service for making autonomous financial decisions and actions."""
    
    def __init__(self):
        self.db = FirebaseDatabase()
        self.collection_name = "autonomous_actions"
        self.max_auto_amount = settings.max_auto_action_amount
    
    async def suggest_actions(self, user_id: str) -> Dict[str, Any]:
        """Suggest actions for a user based on their current financial situation."""
        # Get user information
        user_data = self.db.get_document("users", user_id)
        if not user_data:
            return {"suggestions": [], "error": "User not found"}
        
        user = User.from_firebase_dict(user_data)
        
        # Get latest prediction
        predictions = self.db.get_user_documents("cashflow_predictions", user_id)
        if not predictions:
            return {"suggestions": [], "error": "No cashflow prediction available"}
        
        latest_prediction = max(predictions, key=lambda x: x.get("prediction_date", ""))
        prediction = CashflowPrediction.from_firebase_dict(latest_prediction)
        
        suggestions = []
        
        # Shortfall mitigation actions
        if prediction.shortfall_probability > 0.6:
            suggestions.append({
                "action_type": ActionType.SAVE_TO_EMERGENCY.value,
                "amount": min(prediction.shortfall_amount * 0.3, self.max_auto_amount),
                "reason": "Reduce shortfall risk",
                "priority": "high",
                "risk_level": ActionRiskLevel.LOW.value
            })
        
        # Savings opportunity actions
        if prediction.predicted_balance > 2000 and prediction.shortfall_probability < 0.3:
            suggestions.append({
                "action_type": ActionType.SAVE_TO_EMERGENCY.value,
                "amount": min(prediction.predicted_balance * 0.1, self.max_auto_amount),
                "reason": "Build emergency fund",
                "priority": "medium",
                "risk_level": ActionRiskLevel.LOW.value
            })
        
        # Subscription management
        if prediction.predicted_balance < 1000:
            suggestions.append({
                "action_type": ActionType.PAUSE_SUBSCRIPTION.value,
                "reason": "Conserve cash during low balance",
                "priority": "medium",
                "risk_level": ActionRiskLevel.LOW.value
            })
        
        return {
            "suggestions": suggestions,
            "user_auto_actions_enabled": user.auto_actions_enabled,
            "max_auto_amount": user.max_auto_action_amount,
            "prediction_id": prediction.prediction_id
        }
    
    async def create_action(self, user_id: str, action_data: Dict[str, Any]) -> AutonomousAction:
        """Create a new autonomous action."""
        action_id = str(uuid.uuid4())
        
        # Determine risk level and confirmation requirements
        action_type = ActionType(action_data["action_type"])
        amount = action_data.get("amount", 0)
        
        risk_level, requires_confirmation = self._assess_action_risk(action_type, amount)
        
        action = AutonomousAction(
            action_id=action_id,
            user_id=user_id,
            action_type=action_type,
            action_name=self._get_action_name(action_type),
            description=self._get_action_description(action_type, amount),
            amount=amount,
            source_account=action_data.get("source_account"),
            destination_account=action_data.get("destination_account"),
            action_parameters=action_data.get("action_parameters", {}),
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            max_amount=self.max_auto_amount,
            trigger_reason=action_data.get("reason", "User requested"),
            status=ActionStatus.PENDING,
            scheduled_for=action_data.get("scheduled_for"),
            can_be_reversed=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        success = self.db.create_document(
            self.collection_name,
            action_id,
            action.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to create action in database")
        
        return action
    
    async def get_user_actions(self, user_id: str, status_filter: Optional[ActionStatus] = None, 
                             limit: int = 20) -> List[AutonomousAction]:
        """Get user's actions with optional filtering."""
        actions_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Apply status filter
        if status_filter:
            actions_data = [a for a in actions_data if a.get("status") == status_filter.value]
        
        # Sort by created_at (newest first) and limit
        actions_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        actions_data = actions_data[:limit]
        
        return [AutonomousAction.from_firebase_dict(a) for a in actions_data]
    
    async def get_action(self, action_id: str) -> Optional[AutonomousAction]:
        """Get action by ID."""
        action_data = self.db.get_document(self.collection_name, action_id)
        if not action_data:
            return None
        
        return AutonomousAction.from_firebase_dict(action_data)
    
    async def update_action(self, action_id: str, user_id: str, 
                          update_data: Dict[str, Any]) -> Optional[AutonomousAction]:
        """Update action with user response or status change."""
        action = await self.get_action(action_id)
        if not action or action.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(action, key):
                setattr(action, key, value)
        
        action.updated_at = datetime.utcnow()
        
        # Save to database
        success = self.db.update_document(
            self.collection_name,
            action_id,
            action.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update action in database")
        
        return action
    
    async def confirm_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """Confirm a pending action."""
        action = await self.get_action(action_id)
        if not action or action.user_id != user_id:
            raise Exception("Action not found")
        
        if action.status != ActionStatus.PENDING:
            raise Exception("Action is not pending")
        
        if not action.requires_confirmation:
            raise Exception("Action does not require confirmation")
        
        # Update action status
        action.user_confirmed = True
        action.user_confirmed_at = datetime.utcnow()
        action.status = ActionStatus.PENDING  # Ready for execution
        
        # Save to database
        self.db.update_document(
            self.collection_name,
            action_id,
            action.to_firebase_dict()
        )
        
        return {
            "action_id": action_id,
            "confirmed": True,
            "confirmed_at": action.user_confirmed_at.isoformat()
        }
    
    async def execute_action(self, action_id: str, user_id: str) -> Dict[str, Any]:
        """Execute a pending action."""
        action = await self.get_action(action_id)
        if not action or action.user_id != user_id:
            raise Exception("Action not found")
        
        if not action.can_execute:
            raise Exception("Action cannot be executed at this time")
        
        # Update status to executing
        action.status = ActionStatus.EXECUTING
        action.executed_at = datetime.utcnow()
        
        self.db.update_document(
            self.collection_name,
            action_id,
            action.to_firebase_dict()
        )
        
        try:
            # Execute the actual action based on type
            execution_result = await self._execute_action_by_type(action)
            
            # Update action with result
            action.status = ActionStatus.COMPLETED
            action.completed_at = datetime.utcnow()
            action.execution_result = execution_result
            
            self.db.update_document(
                self.collection_name,
                action_id,
                action.to_firebase_dict()
            )
            
            return {
                "action_id": action_id,
                "executed": True,
                "executed_at": action.executed_at.isoformat(),
                "result": execution_result
            }
            
        except Exception as e:
            # Update action with error
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            
            self.db.update_document(
                self.collection_name,
                action_id,
                action.to_firebase_dict()
            )
            
            raise Exception(f"Failed to execute action: {str(e)}")
    
    async def reverse_action(self, action_id: str, user_id: str, reason: str) -> Dict[str, Any]:
        """Reverse a completed action."""
        action = await self.get_action(action_id)
        if not action or action.user_id != user_id:
            raise Exception("Action not found")
        
        if not action.is_reversible:
            raise Exception("Action cannot be reversed")
        
        if action.status != ActionStatus.COMPLETED:
            raise Exception("Only completed actions can be reversed")
        
        # Update action status
        action.status = ActionStatus.REVERSED
        action.reversed_at = datetime.utcnow()
        action.reversal_reason = reason
        
        # TODO: Execute actual reversal based on action type
        
        self.db.update_document(
            self.collection_name,
            action_id,
            action.to_firebase_dict()
        )
        
        return {
            "action_id": action_id,
            "reversed": True,
            "reversed_at": action.reversed_at.isoformat(),
            "reason": reason
        }
    
    async def get_action_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get action effectiveness analytics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        actions_data = self.db.get_user_documents(self.collection_name, user_id)
        
        # Filter by date
        recent_actions = [
            a for a in actions_data 
            if datetime.fromisoformat(a.get("created_at", "")) >= cutoff_date
        ]
        
        if not recent_actions:
            return {
                "period_days": days,
                "total_actions": 0,
                "completed_actions": 0,
                "failed_actions": 0,
                "reversed_actions": 0,
                "success_rate": 0,
                "average_effectiveness": 0,
                "action_types": {},
                "insights": []
            }
        
        # Calculate metrics
        total_actions = len(recent_actions)
        completed_actions = len([a for a in recent_actions if a.get("status") == "completed"])
        failed_actions = len([a for a in recent_actions if a.get("status") == "failed"])
        reversed_actions = len([a for a in recent_actions if a.get("status") == "reversed"])
        
        success_rate = (completed_actions / max(total_actions, 1)) * 100
        
        # Calculate average effectiveness
        effectiveness_scores = [a.get("effectiveness_score") for a in recent_actions if a.get("effectiveness_score")]
        average_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
        
        # Action type breakdown
        action_types = {}
        for action in recent_actions:
            action_type = action.get("action_type", "unknown")
            if action_type not in action_types:
                action_types[action_type] = {"total": 0, "completed": 0, "failed": 0}
            action_types[action_type]["total"] += 1
            if action.get("status") == "completed":
                action_types[action_type]["completed"] += 1
            elif action.get("status") == "failed":
                action_types[action_type]["failed"] += 1
        
        # Generate insights
        insights = self._generate_action_insights(
            total_actions, completed_actions, failed_actions, 
            success_rate, average_effectiveness
        )
        
        return {
            "period_days": days,
            "total_actions": total_actions,
            "completed_actions": completed_actions,
            "failed_actions": failed_actions,
            "reversed_actions": reversed_actions,
            "success_rate": success_rate,
            "average_effectiveness": average_effectiveness,
            "action_types": action_types,
            "insights": insights
        }
    
    def _assess_action_risk(self, action_type: ActionType, amount: float) -> tuple[ActionRiskLevel, bool]:
        """Assess the risk level and confirmation requirements for an action."""
        # Low risk actions
        if action_type in [ActionType.SAVE_TO_EMERGENCY, ActionType.SAVE_TO_GOAL]:
            if amount <= 500:
                return ActionRiskLevel.LOW, False
            else:
                return ActionRiskLevel.LOW, True
        
        # Medium risk actions
        elif action_type in [ActionType.PAUSE_SUBSCRIPTION, ActionType.SCHEDULE_BILL_PAYMENT]:
            return ActionRiskLevel.MEDIUM, True
        
        # High risk actions
        elif action_type in [ActionType.TRANSFER_BETWEEN_ACCOUNTS, ActionType.DISPUTE_TRANSACTION]:
            return ActionRiskLevel.HIGH, True
        
        # Default
        return ActionRiskLevel.MEDIUM, True
    
    def _get_action_name(self, action_type: ActionType) -> str:
        """Get human-readable action name."""
        names = {
            ActionType.SAVE_TO_EMERGENCY: "Save to Emergency Fund",
            ActionType.SAVE_TO_GOAL: "Save to Goal",
            ActionType.TRANSFER_BETWEEN_ACCOUNTS: "Transfer Between Accounts",
            ActionType.PAUSE_SUBSCRIPTION: "Pause Subscription",
            ActionType.SCHEDULE_BILL_PAYMENT: "Schedule Bill Payment",
            ActionType.DISPUTE_TRANSACTION: "Dispute Transaction",
            ActionType.ADJUST_SPENDING_LIMIT: "Adjust Spending Limit"
        }
        return names.get(action_type, "Unknown Action")
    
    def _get_action_description(self, action_type: ActionType, amount: float) -> str:
        """Get action description."""
        descriptions = {
            ActionType.SAVE_TO_EMERGENCY: f"Save ₹{amount:.0f} to emergency fund",
            ActionType.SAVE_TO_GOAL: f"Save ₹{amount:.0f} to savings goal",
            ActionType.TRANSFER_BETWEEN_ACCOUNTS: f"Transfer ₹{amount:.0f} between accounts",
            ActionType.PAUSE_SUBSCRIPTION: "Pause non-essential subscription",
            ActionType.SCHEDULE_BILL_PAYMENT: "Schedule upcoming bill payment",
            ActionType.DISPUTE_TRANSACTION: "Dispute suspicious transaction",
            ActionType.ADJUST_SPENDING_LIMIT: "Adjust spending limit"
        }
        return descriptions.get(action_type, f"Execute {action_type.value} action")
    
    async def _execute_action_by_type(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute action based on its type."""
        if action.action_type == ActionType.SAVE_TO_EMERGENCY:
            return await self._execute_save_to_emergency(action)
        elif action.action_type == ActionType.PAUSE_SUBSCRIPTION:
            return await self._execute_pause_subscription(action)
        elif action.action_type == ActionType.SCHEDULE_BILL_PAYMENT:
            return await self._execute_schedule_bill_payment(action)
        else:
            # For now, return a mock result
            return {
                "action_executed": True,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"{action.action_name} executed successfully"
            }
    
    async def _execute_save_to_emergency(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute save to emergency fund action."""
        # TODO: Implement actual money transfer to emergency fund
        # For now, return mock result
        return {
            "action_executed": True,
            "amount_saved": action.amount,
            "destination": "emergency_fund",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Successfully saved ₹{action.amount:.0f} to emergency fund"
        }
    
    async def _execute_pause_subscription(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute pause subscription action."""
        # TODO: Implement actual subscription pausing
        return {
            "action_executed": True,
            "subscription_paused": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Non-essential subscription paused"
        }
    
    async def _execute_schedule_bill_payment(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute schedule bill payment action."""
        # TODO: Implement actual bill payment scheduling
        return {
            "action_executed": True,
            "payment_scheduled": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Bill payment scheduled"
        }
    
    def _generate_action_insights(self, total_actions: int, completed_actions: int, 
                                failed_actions: int, success_rate: float, 
                                average_effectiveness: float) -> List[str]:
        """Generate insights from action analytics."""
        insights = []
        
        if success_rate > 80:
            insights.append("Excellent! Most of your autonomous actions are completing successfully.")
        elif success_rate > 60:
            insights.append("Good success rate for autonomous actions. Consider reviewing failed actions.")
        else:
            insights.append("Many actions are failing. Check your account connections and settings.")
        
        if average_effectiveness > 4:
            insights.append("The autonomous actions are highly effective. Keep them enabled!")
        elif average_effectiveness < 3:
            insights.append("Consider adjusting your autonomous action settings for better effectiveness.")
        
        if failed_actions > total_actions * 0.3:
            insights.append("High failure rate detected. Check your payment methods and account status.")
        
        return insights
