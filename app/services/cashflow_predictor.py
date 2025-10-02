"""Cashflow prediction service using ML models."""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from app.database import FirebaseDatabase
from app.models.firebase_models import CashflowPrediction, Transaction, TransactionType
from app.config import settings


class CashflowPredictor:
    """Service for predicting user cashflow using ML models."""
    
    def __init__(self):
        self.db = FirebaseDatabase()
        self.prediction_days = settings.cashflow_prediction_days
        self.confidence_threshold = settings.nudge_confidence_threshold
    
    async def predict_cashflow(self, user_id: str, days_ahead: int = None) -> CashflowPrediction:
        """Generate cashflow prediction for a user."""
        if days_ahead is None:
            days_ahead = self.prediction_days
        
        # Get user's transaction history
        transactions = self.db.get_user_documents("transactions", user_id)
        
        if not transactions:
            # No transaction history - create baseline prediction
            return await self._create_baseline_prediction(user_id, days_ahead)
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['amount'] = pd.to_numeric(df['amount'])
        
        # Generate prediction
        prediction_data = await self._generate_prediction_data(df, days_ahead)
        
        # Create prediction object
        prediction = CashflowPrediction(
            prediction_id=str(uuid.uuid4()),
            user_id=user_id,
            prediction_date=datetime.utcnow(),
            forecast_start_date=datetime.utcnow(),
            forecast_end_date=datetime.utcnow() + timedelta(days=days_ahead),
            predicted_balance=prediction_data['predicted_balance'],
            confidence_level=prediction_data['confidence_level'],
            shortfall_probability=prediction_data['shortfall_probability'],
            shortfall_amount=prediction_data.get('shortfall_amount'),
            daily_forecasts=prediction_data['daily_forecasts'],
            liquidity_risk_score=prediction_data['liquidity_risk_score'],
            income_uncertainty=prediction_data['income_uncertainty'],
            expense_volatility=prediction_data['expense_volatility'],
            model_version="v1.0",
            model_features=prediction_data.get('features', {}),
            prediction_reasoning=prediction_data.get('reasoning', '')
        )
        
        # Save prediction to database
        self.db.create_document(
            "cashflow_predictions",
            prediction.prediction_id,
            prediction.to_firebase_dict()
        )
        
        return prediction
    
    async def _generate_prediction_data(self, df: pd.DataFrame, days_ahead: int) -> Dict[str, Any]:
        """Generate prediction data from transaction history."""
        # Get current balance (simplified - in real implementation, get from bank API)
        current_balance = self._estimate_current_balance(df)
        
        # Analyze income patterns
        income_patterns = self._analyze_income_patterns(df)
        
        # Analyze expense patterns
        expense_patterns = self._analyze_expense_patterns(df)
        
        # Generate daily forecasts
        daily_forecasts = self._generate_daily_forecasts(
            current_balance, income_patterns, expense_patterns, days_ahead
        )
        
        # Calculate risk metrics
        final_balance = daily_forecasts[-1]['balance']
        shortfall_probability = max(0, min(1, (current_balance - final_balance) / max(current_balance, 1000)))
        
        # Calculate confidence based on data quality and patterns
        confidence_level = self._calculate_confidence(df, income_patterns, expense_patterns)
        
        # Calculate liquidity risk
        liquidity_risk = self._calculate_liquidity_risk(daily_forecasts, current_balance)
        
        return {
            'predicted_balance': final_balance,
            'confidence_level': confidence_level,
            'shortfall_probability': shortfall_probability,
            'shortfall_amount': max(0, -final_balance) if final_balance < 0 else None,
            'daily_forecasts': daily_forecasts,
            'liquidity_risk_score': liquidity_risk,
            'income_uncertainty': income_patterns.get('uncertainty', 0.5),
            'expense_volatility': expense_patterns.get('volatility', 0.3),
            'features': {
                'transaction_count': len(df),
                'days_of_data': (df['transaction_date'].max() - df['transaction_date'].min()).days,
                'income_frequency': income_patterns.get('frequency', 0),
                'expense_frequency': expense_patterns.get('frequency', 0)
            },
            'reasoning': self._generate_reasoning(income_patterns, expense_patterns, shortfall_probability)
        }
    
    def _estimate_current_balance(self, df: pd.DataFrame) -> float:
        """Estimate current balance from transaction history."""
        # Simple estimation - sum of all income minus expenses
        income = df[df['transaction_type'] == TransactionType.INCOME.value]['amount'].sum()
        expenses = df[df['transaction_type'] == TransactionType.EXPENSE.value]['amount'].sum()
        return income - expenses
    
    def _analyze_income_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze income patterns from transaction data."""
        income_df = df[df['transaction_type'] == TransactionType.INCOME.value].copy()
        
        if income_df.empty:
            return {'frequency': 0, 'average_amount': 0, 'uncertainty': 0.8}
        
        # Calculate income frequency (days between income events)
        income_df = income_df.sort_values('transaction_date')
        if len(income_df) > 1:
            gaps = income_df['transaction_date'].diff().dt.days.dropna()
            avg_gap = gaps.mean()
            frequency = 30 / max(avg_gap, 1)  # Income events per month
        else:
            frequency = 0.5  # Conservative estimate
        
        # Calculate average amount and variability
        avg_amount = income_df['amount'].mean()
        amount_std = income_df['amount'].std()
        uncertainty = min(0.9, amount_std / max(avg_amount, 1)) if avg_amount > 0 else 0.8
        
        return {
            'frequency': frequency,
            'average_amount': avg_amount,
            'uncertainty': uncertainty,
            'last_amount': income_df['amount'].iloc[-1] if not income_df.empty else 0
        }
    
    def _analyze_expense_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze expense patterns from transaction data."""
        expense_df = df[df['transaction_type'] == TransactionType.EXPENSE.value].copy()
        
        if expense_df.empty:
            return {'frequency': 0, 'average_daily': 0, 'volatility': 0.3}
        
        # Calculate daily expenses
        expense_df['date'] = expense_df['transaction_date'].dt.date
        daily_expenses = expense_df.groupby('date')['amount'].sum()
        
        avg_daily = daily_expenses.mean()
        daily_std = daily_expenses.std()
        volatility = min(0.9, daily_std / max(avg_daily, 1)) if avg_daily > 0 else 0.5
        
        # Calculate frequency (expense events per day)
        frequency = len(expense_df) / max((df['transaction_date'].max() - df['transaction_date'].min()).days, 1)
        
        return {
            'frequency': frequency,
            'average_daily': avg_daily,
            'volatility': volatility,
            'total_expenses': expense_df['amount'].sum()
        }
    
    def _generate_daily_forecasts(self, current_balance: float, income_patterns: Dict, 
                                 expense_patterns: Dict, days_ahead: int) -> List[Dict[str, Any]]:
        """Generate daily balance forecasts."""
        forecasts = []
        balance = current_balance
        
        for day in range(days_ahead):
            date = datetime.utcnow() + timedelta(days=day)
            
            # Predict income for this day (simplified model)
            expected_income = self._predict_daily_income(day, income_patterns)
            
            # Predict expenses for this day
            expected_expenses = self._predict_daily_expenses(day, expense_patterns)
            
            # Update balance
            balance += expected_income - expected_expenses
            
            # Calculate confidence for this day (decreases over time)
            day_confidence = max(0.1, 1.0 - (day * 0.02))
            
            forecasts.append({
                'date': date.isoformat(),
                'balance': round(balance, 2),
                'expected_income': round(expected_income, 2),
                'expected_expenses': round(expected_expenses, 2),
                'confidence': round(day_confidence, 2)
            })
        
        return forecasts
    
    def _predict_daily_income(self, day: int, income_patterns: Dict) -> float:
        """Predict income for a specific day."""
        frequency = income_patterns.get('frequency', 0.5)
        avg_amount = income_patterns.get('average_amount', 0)
        
        # Simple probability model
        if frequency > 0:
            daily_probability = min(1.0, frequency / 30)
            if np.random.random() < daily_probability:
                # Add some variability
                uncertainty = income_patterns.get('uncertainty', 0.5)
                variability = np.random.normal(1, uncertainty * 0.3)
                return max(0, avg_amount * variability)
        
        return 0
    
    def _predict_daily_expenses(self, day: int, expense_patterns: Dict) -> float:
        """Predict expenses for a specific day."""
        avg_daily = expense_patterns.get('average_daily', 0)
        volatility = expense_patterns.get('volatility', 0.3)
        
        # Add some randomness based on volatility
        variability = np.random.normal(1, volatility * 0.2)
        return max(0, avg_daily * variability)
    
    def _calculate_confidence(self, df: pd.DataFrame, income_patterns: Dict, expense_patterns: Dict) -> float:
        """Calculate prediction confidence based on data quality."""
        # Base confidence on amount of data
        data_confidence = min(1.0, len(df) / 100)
        
        # Adjust based on pattern clarity
        income_clarity = 1.0 - income_patterns.get('uncertainty', 0.5)
        expense_clarity = 1.0 - expense_patterns.get('volatility', 0.5)
        
        # Combine factors
        confidence = (data_confidence * 0.4 + income_clarity * 0.3 + expense_clarity * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_liquidity_risk(self, daily_forecasts: List[Dict], current_balance: float) -> float:
        """Calculate liquidity risk score."""
        if not daily_forecasts:
            return 0.5
        
        # Count days with negative balance
        negative_days = sum(1 for forecast in daily_forecasts if forecast['balance'] < 0)
        total_days = len(daily_forecasts)
        
        # Calculate risk based on negative balance frequency and severity
        risk_from_frequency = negative_days / total_days
        
        # Risk from minimum balance
        min_balance = min(forecast['balance'] for forecast in daily_forecasts)
        risk_from_severity = max(0, -min_balance / max(current_balance, 1000))
        
        return min(1.0, (risk_from_frequency * 0.6 + risk_from_severity * 0.4))
    
    def _generate_reasoning(self, income_patterns: Dict, expense_patterns: Dict, shortfall_probability: float) -> str:
        """Generate human-readable reasoning for the prediction."""
        reasoning_parts = []
        
        # Income analysis
        income_freq = income_patterns.get('frequency', 0)
        income_uncertainty = income_patterns.get('uncertainty', 0.5)
        
        if income_freq > 0:
            if income_uncertainty > 0.7:
                reasoning_parts.append("Your income shows high variability, making predictions less certain.")
            elif income_uncertainty < 0.3:
                reasoning_parts.append("Your income pattern is relatively stable.")
            else:
                reasoning_parts.append("Your income has moderate variability.")
        
        # Expense analysis
        expense_volatility = expense_patterns.get('volatility', 0.3)
        if expense_volatility > 0.6:
            reasoning_parts.append("Your spending varies significantly from day to day.")
        elif expense_volatility < 0.3:
            reasoning_parts.append("Your spending is quite consistent.")
        
        # Shortfall analysis
        if shortfall_probability > 0.7:
            reasoning_parts.append("There's a high risk of running low on funds in the coming days.")
        elif shortfall_probability > 0.4:
            reasoning_parts.append("There's a moderate risk of cash flow issues.")
        else:
            reasoning_parts.append("Your cash flow outlook appears stable.")
        
        return " ".join(reasoning_parts) if reasoning_parts else "Based on your transaction history, here's your cash flow forecast."
    
    async def _create_baseline_prediction(self, user_id: str, days_ahead: int) -> CashflowPrediction:
        """Create a baseline prediction for users with no transaction history."""
        prediction = CashflowPrediction(
            prediction_id=str(uuid.uuid4()),
            user_id=user_id,
            prediction_date=datetime.utcnow(),
            forecast_start_date=datetime.utcnow(),
            forecast_end_date=datetime.utcnow() + timedelta(days=days_ahead),
            predicted_balance=0.0,
            confidence_level=0.1,  # Very low confidence without data
            shortfall_probability=0.5,  # Neutral assumption
            daily_forecasts=[{
                'date': (datetime.utcnow() + timedelta(days=i)).isoformat(),
                'balance': 0.0,
                'expected_income': 0.0,
                'expected_expenses': 0.0,
                'confidence': 0.1
            } for i in range(days_ahead)],
            liquidity_risk_score=0.5,
            income_uncertainty=0.8,
            expense_volatility=0.5,
            model_version="v1.0",
            model_features={'baseline': True},
            prediction_reasoning="No transaction history available. Add transactions to get personalized predictions."
        )
        
        # Save prediction
        self.db.create_document(
            "cashflow_predictions",
            prediction.prediction_id,
            prediction.to_firebase_dict()
        )
        
        return prediction
