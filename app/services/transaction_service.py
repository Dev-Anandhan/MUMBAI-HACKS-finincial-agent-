"""Transaction service for managing transaction operations."""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from app.database import FirebaseDatabase
from app.models.firebase_models import Transaction, TransactionType, TransactionCategory


class TransactionService:
    """Service for transaction-related operations."""
    
    def __init__(self, db: FirebaseDatabase):
        self.db = db
        self.collection_name = "transactions"
    
    async def create_transaction(self, user_id: str, transaction_data: Dict[str, Any]) -> Transaction:
        """Create a new transaction."""
        transaction_id = str(uuid.uuid4())
        
        # Parse transaction date
        transaction_date = datetime.fromisoformat(transaction_data["transaction_date"])
        
        # Create transaction object
        transaction = Transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=transaction_data["amount"],
            currency=transaction_data.get("currency", "INR"),
            transaction_type=TransactionType(transaction_data["transaction_type"]),
            category=TransactionCategory(transaction_data.get("category", TransactionCategory.UNKNOWN)),
            description=transaction_data.get("description"),
            merchant_name=transaction_data.get("merchant_name"),
            transaction_date=transaction_date,
            source_account=transaction_data.get("source_account"),
            source_type=transaction_data.get("source_type", "manual"),
            location=transaction_data.get("location"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Auto-classify transaction if possible
        await self._auto_classify_transaction(transaction)
        
        # Save to Firebase
        success = self.db.create_document(
            self.collection_name,
            transaction_id,
            transaction.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to create transaction in database")
        
        return transaction
    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        transaction_data = self.db.get_document(self.collection_name, transaction_id)
        if not transaction_data:
            return None
        
        return Transaction.from_firebase_dict(transaction_data)
    
    async def get_user_transactions(self, user_id: str, limit: int = 50, offset: int = 0,
                                  transaction_type: Optional[TransactionType] = None,
                                  category: Optional[TransactionCategory] = None) -> List[Transaction]:
        """Get user's transactions with filtering."""
        # Get all user transactions
        all_transactions = self.db.get_user_documents(self.collection_name, user_id)
        
        # Apply filters
        filtered_transactions = []
        for t_data in all_transactions:
            # Check transaction type filter
            if transaction_type and t_data.get("transaction_type") != transaction_type.value:
                continue
            
            # Check category filter
            if category and t_data.get("category") != category.value:
                continue
            
            # Skip deleted transactions
            if t_data.get("is_deleted", False):
                continue
            
            filtered_transactions.append(Transaction.from_firebase_dict(t_data))
        
        # Sort by transaction date (newest first)
        filtered_transactions.sort(key=lambda x: x.transaction_date, reverse=True)
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        return filtered_transactions[start_idx:end_idx]
    
    async def update_transaction(self, transaction_id: str, user_id: str, 
                               update_data: Dict[str, Any]) -> Optional[Transaction]:
        """Update transaction information."""
        # Get existing transaction
        transaction = await self.get_transaction(transaction_id)
        if not transaction or transaction.user_id != user_id:
            return None
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        transaction.updated_at = datetime.utcnow()
        
        # Save to Firebase
        success = self.db.update_document(
            self.collection_name,
            transaction_id,
            transaction.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update transaction in database")
        
        return transaction
    
    async def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """Delete transaction (soft delete)."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction or transaction.user_id != user_id:
            return False
        
        # Soft delete by setting is_deleted to True
        transaction.is_deleted = True
        transaction.updated_at = datetime.utcnow()
        
        success = self.db.update_document(
            self.collection_name,
            transaction_id,
            transaction.to_firebase_dict()
        )
        
        return success
    
    async def create_bulk_transactions(self, user_id: str, transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple transactions at once."""
        created_transactions = []
        failed_transactions = []
        
        for t_data in transactions_data:
            try:
                transaction = await self.create_transaction(user_id, t_data)
                created_transactions.append(transaction.transaction_id)
            except Exception as e:
                failed_transactions.append({
                    "data": t_data,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "created_count": len(created_transactions),
            "failed_count": len(failed_transactions),
            "created_transaction_ids": created_transactions,
            "failed_transactions": failed_transactions
        }
    
    async def get_transaction_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get transaction analytics and insights."""
        # Get transactions from the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        all_transactions = self.db.get_user_documents(self.collection_name, user_id)
        
        # Filter by date and convert to DataFrame for analysis
        recent_transactions = []
        for t_data in all_transactions:
            if not t_data.get("is_deleted", False):
                t_date = datetime.fromisoformat(t_data["transaction_date"])
                if t_date >= cutoff_date:
                    recent_transactions.append(t_data)
        
        if not recent_transactions:
            return {
                "period_days": days,
                "total_transactions": 0,
                "total_income": 0,
                "total_expenses": 0,
                "net_worth": 0,
                "category_breakdown": {},
                "daily_averages": {},
                "insights": []
            }
        
        df = pd.DataFrame(recent_transactions)
        df['amount'] = pd.to_numeric(df['amount'])
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Calculate basic metrics
        income_transactions = df[df['transaction_type'] == TransactionType.INCOME.value]
        expense_transactions = df[df['transaction_type'] == TransactionType.EXPENSE.value]
        
        total_income = income_transactions['amount'].sum()
        total_expenses = expense_transactions['amount'].sum()
        net_worth = total_income - total_expenses
        
        # Category breakdown
        category_breakdown = {}
        for _, row in df.iterrows():
            category = row.get('category', 'unknown')
            amount = row['amount']
            if category not in category_breakdown:
                category_breakdown[category] = {'count': 0, 'total': 0}
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['total'] += amount
        
        # Daily averages
        daily_income = total_income / days
        daily_expenses = total_expenses / days
        
        # Generate insights
        insights = self._generate_insights(df, total_income, total_expenses, category_breakdown)
        
        return {
            "period_days": days,
            "total_transactions": len(df),
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_worth": float(net_worth),
            "category_breakdown": category_breakdown,
            "daily_averages": {
                "income": float(daily_income),
                "expenses": float(daily_expenses),
                "net": float(daily_income - daily_expenses)
            },
            "insights": insights
        }
    
    async def classify_transaction(self, transaction_id: str, user_id: str) -> Dict[str, Any]:
        """Manually classify a transaction."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction or transaction.user_id != user_id:
            raise Exception("Transaction not found")
        
        # Run classification logic
        await self._auto_classify_transaction(transaction)
        
        # Update transaction
        success = self.db.update_document(
            self.collection_name,
            transaction_id,
            transaction.to_firebase_dict()
        )
        
        if not success:
            raise Exception("Failed to update transaction classification")
        
        return {
            "transaction_id": transaction_id,
            "classified_category": transaction.category.value,
            "confidence_score": transaction.confidence_score,
            "is_essential": transaction.is_essential,
            "is_recurring": transaction.is_recurring
        }
    
    async def _auto_classify_transaction(self, transaction: Transaction):
        """Auto-classify transaction using simple rules and ML."""
        # Simple rule-based classification
        description = (transaction.description or "").lower()
        merchant = (transaction.merchant_name or "").lower()
        
        # Income classification
        if transaction.transaction_type == TransactionType.INCOME:
            if any(word in description for word in ["salary", "wage", "pay", "bonus"]):
                transaction.category = TransactionCategory.SALARY
                transaction.confidence_score = 0.9
            elif any(word in description for word in ["gig", "freelance", "contract"]):
                transaction.category = TransactionCategory.GIG_INCOME
                transaction.confidence_score = 0.8
            else:
                transaction.category = TransactionCategory.INVESTMENT_RETURN
                transaction.confidence_score = 0.6
        
        # Expense classification
        elif transaction.transaction_type == TransactionType.EXPENSE:
            # Essential expenses
            if any(word in description + merchant for word in ["rent", "house", "apartment"]):
                transaction.category = TransactionCategory.RENT
                transaction.is_essential = True
                transaction.confidence_score = 0.9
            elif any(word in description + merchant for word in ["electricity", "water", "gas", "utility"]):
                transaction.category = TransactionCategory.UTILITIES
                transaction.is_essential = True
                transaction.confidence_score = 0.9
            elif any(word in description + merchant for word in ["grocery", "supermarket", "food"]):
                transaction.category = TransactionCategory.GROCERIES
                transaction.is_essential = True
                transaction.confidence_score = 0.8
            elif any(word in description + merchant for word in ["transport", "uber", "taxi", "bus", "metro"]):
                transaction.category = TransactionCategory.TRANSPORT
                transaction.is_essential = True
                transaction.confidence_score = 0.8
            elif any(word in description + merchant for word in ["hospital", "clinic", "pharmacy", "medical"]):
                transaction.category = TransactionCategory.HEALTHCARE
                transaction.is_essential = True
                transaction.confidence_score = 0.8
            # Discretionary expenses
            elif any(word in description + merchant for word in ["restaurant", "cafe", "food delivery"]):
                transaction.category = TransactionCategory.DINING
                transaction.is_essential = False
                transaction.confidence_score = 0.8
            elif any(word in description + merchant for word in ["movie", "entertainment", "game"]):
                transaction.category = TransactionCategory.ENTERTAINMENT
                transaction.is_essential = False
                transaction.confidence_score = 0.7
            elif any(word in description + merchant for word in ["netflix", "spotify", "subscription"]):
                transaction.category = TransactionCategory.SUBSCRIPTIONS
                transaction.is_essential = False
                transaction.is_recurring = True
                transaction.confidence_score = 0.8
            else:
                transaction.category = TransactionCategory.UNKNOWN
                transaction.confidence_score = 0.3
        
        # Update ML features
        transaction.ml_features = {
            "description_length": len(description),
            "has_merchant": bool(merchant),
            "amount_range": self._get_amount_range(transaction.amount),
            "time_of_day": transaction.transaction_date.hour
        }
    
    def _get_amount_range(self, amount: float) -> str:
        """Get amount range category."""
        if amount < 100:
            return "small"
        elif amount < 1000:
            return "medium"
        elif amount < 10000:
            return "large"
        else:
            return "very_large"
    
    def _generate_insights(self, df: pd.DataFrame, total_income: float, 
                          total_expenses: float, category_breakdown: Dict) -> List[str]:
        """Generate insights from transaction data."""
        insights = []
        
        # Spending vs income insight
        if total_expenses > total_income * 0.8:
            insights.append("Your expenses are quite high relative to your income. Consider reviewing discretionary spending.")
        elif total_expenses < total_income * 0.5:
            insights.append("Great job! You're spending well below your income. This is excellent for building savings.")
        
        # Category insights
        if TransactionCategory.DINING.value in category_breakdown:
            dining_total = category_breakdown[TransactionCategory.DINING.value]['total']
            if dining_total > total_expenses * 0.2:
                insights.append("You're spending a significant portion on dining out. Consider cooking at home more often.")
        
        if TransactionCategory.ENTERTAINMENT.value in category_breakdown:
            entertainment_total = category_breakdown[TransactionCategory.ENTERTAINMENT.value]['total']
            if entertainment_total > total_expenses * 0.15:
                insights.append("Entertainment spending is high. Look for free or low-cost alternatives.")
        
        # Recurring expenses insight
        recurring_categories = [TransactionCategory.RENT.value, TransactionCategory.UTILITIES.value, 
                              TransactionCategory.SUBSCRIPTIONS.value]
        recurring_total = sum(category_breakdown.get(cat, {}).get('total', 0) for cat in recurring_categories)
        if recurring_total > total_expenses * 0.6:
            insights.append("Most of your expenses are recurring. This is good for predictability but leaves less flexibility.")
        
        return insights
