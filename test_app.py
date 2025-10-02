"""
Simple test version of Financial Agent for demonstration
Works without heavy dependencies like pandas, firebase, etc.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta
import random
import uuid

# Simple in-memory storage for testing
users_db = {}
transactions_db = {}
predictions_db = {}
nudges_db = {}

app = FastAPI(
    title="Financial Agent - Test Version",
    description="Simplified version for testing core functionality",
    version="1.0.0"
)

# Pydantic models
class User(BaseModel):
    user_id: str
    phone_number: str
    name: str
    income_schedule: str = "irregular"
    risk_tolerance: str = "conservative"
    auto_actions_enabled: bool = False

class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    transaction_type: str  # "income" or "expense"
    category: str
    description: str
    transaction_date: str

class CashflowPrediction(BaseModel):
    prediction_id: str
    user_id: str
    predicted_balance: float
    shortfall_probability: float
    confidence_level: float
    reasoning: str

class Nudge(BaseModel):
    nudge_id: str
    user_id: str
    title: str
    message: str
    nudge_type: str
    priority: str
    suggested_action: Optional[Dict[str, Any]] = None

# Helper functions
def calculate_balance(user_id: str) -> float:
    """Calculate current balance for a user."""
    balance = 0.0
    for transaction in transactions_db.values():
        if transaction["user_id"] == user_id:
            if transaction["transaction_type"] == "income":
                balance += transaction["amount"]
            else:
                balance -= transaction["amount"]
    return balance

def generate_prediction(user_id: str) -> CashflowPrediction:
    """Generate a simple cashflow prediction."""
    current_balance = calculate_balance(user_id)
    
    # Simple prediction logic
    user_transactions = [t for t in transactions_db.values() if t["user_id"] == user_id]
    
    if len(user_transactions) < 3:
        # Not enough data
        predicted_balance = current_balance - 500  # Conservative estimate
        shortfall_probability = 0.4
        confidence_level = 0.3
        reasoning = "Limited transaction history. Conservative prediction based on typical spending patterns."
    else:
        # Simple trend analysis
        recent_income = sum(t["amount"] for t in user_transactions[-10:] if t["transaction_type"] == "income")
        recent_expenses = sum(t["amount"] for t in user_transactions[-10:] if t["transaction_type"] == "expense")
        
        daily_expense_rate = recent_expenses / max(len([t for t in user_transactions[-10:] if t["transaction_type"] == "expense"]), 1)
        predicted_balance = current_balance - (daily_expense_rate * 7)  # 7-day prediction
        
        shortfall_probability = max(0, min(1, (current_balance - predicted_balance) / max(current_balance, 1000)))
        confidence_level = min(0.9, len(user_transactions) / 50)
        
        if shortfall_probability > 0.7:
            reasoning = f"High risk of shortfall in next 7 days. Predicted balance: ₹{predicted_balance:.0f}. Consider reducing discretionary spending."
        elif shortfall_probability > 0.4:
            reasoning = f"Moderate risk of cash flow issues. Predicted balance: ₹{predicted_balance:.0f}. Monitor your spending."
        else:
            reasoning = f"Cash flow looks stable. Predicted balance: ₹{predicted_balance:.0f}. Good job managing your finances!"
    
    prediction_id = str(uuid.uuid4())
    prediction = CashflowPrediction(
        prediction_id=prediction_id,
        user_id=user_id,
        predicted_balance=predicted_balance,
        shortfall_probability=shortfall_probability,
        confidence_level=confidence_level,
        reasoning=reasoning
    )
    
    predictions_db[prediction_id] = prediction.dict()
    return prediction

def generate_nudges(user_id: str) -> List[Nudge]:
    """Generate nudges based on user's financial situation."""
    nudges = []
    current_balance = calculate_balance(user_id)
    user_transactions = [t for t in transactions_db.values() if t["user_id"] == user_id]
    
    # Low balance nudge
    if current_balance < 1000:
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="Low Balance Alert",
            message=f"Your current balance is ₹{current_balance:.0f}. Consider being extra careful with spending.",
            nudge_type="informational",
            priority="high"
        )
        nudges.append(nudge)
        nudges_db[nudge.nudge_id] = nudge.dict()
    
    # High spending nudge
    recent_expenses = sum(t["amount"] for t in user_transactions[-5:] if t["transaction_type"] == "expense")
    if recent_expenses > 2000:
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="High Spending Alert",
            message=f"You've spent ₹{recent_expenses:.0f} in the last 5 transactions. Consider reviewing your expenses.",
            nudge_type="informational",
            priority="medium"
        )
        nudges.append(nudge)
        nudges_db[nudge.nudge_id] = nudge.dict()
    
    # Savings opportunity nudge
    if current_balance > 3000:
        savings_amount = min(500, current_balance * 0.1)
        nudge = Nudge(
            nudge_id=str(uuid.uuid4()),
            user_id=user_id,
            title="Savings Opportunity",
            message=f"You have ₹{current_balance:.0f} available. Consider saving ₹{savings_amount:.0f} to your emergency fund.",
            nudge_type="actionable",
            priority="low",
            suggested_action={
                "type": "save_to_emergency",
                "amount": savings_amount,
                "description": "Save to emergency fund"
            }
        )
        nudges.append(nudge)
        nudges_db[nudge.nudge_id] = nudge.dict()
    
    return nudges

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Financial Agent API - Test Version",
        "description": "Simplified version for testing core functionality",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "users": "/users",
            "transactions": "/transactions", 
            "predictions": "/predictions",
            "nudges": "/nudges"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "financial-agent-test",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# User endpoints
@app.post("/users/", status_code=201)
async def create_user(user_data: User):
    """Create a new user."""
    users_db[user_data.user_id] = user_data.dict()
    return {"message": "User created successfully", "user_id": user_data.user_id}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

# Transaction endpoints
@app.post("/transactions/", status_code=201)
async def create_transaction(transaction_data: Transaction):
    """Create a new transaction."""
    transactions_db[transaction_data.transaction_id] = transaction_data.dict()
    return {"message": "Transaction created successfully", "transaction_id": transaction_data.transaction_id}

@app.get("/transactions/{user_id}")
async def get_user_transactions(user_id: str):
    """Get all transactions for a user."""
    user_transactions = [t for t in transactions_db.values() if t["user_id"] == user_id]
    return {"transactions": user_transactions, "count": len(user_transactions)}

@app.get("/transactions/{user_id}/balance")
async def get_user_balance(user_id: str):
    """Get current balance for a user."""
    balance = calculate_balance(user_id)
    return {"user_id": user_id, "current_balance": balance}

# Prediction endpoints
@app.post("/predictions/", status_code=201)
async def create_prediction(user_id: str):
    """Generate a new cashflow prediction for a user."""
    prediction = generate_prediction(user_id)
    return prediction

@app.get("/predictions/{user_id}/latest")
async def get_latest_prediction(user_id: str):
    """Get the latest prediction for a user."""
    user_predictions = [p for p in predictions_db.values() if p["user_id"] == user_id]
    if not user_predictions:
        # Generate new prediction if none exists
        prediction = generate_prediction(user_id)
        return prediction
    
    latest_prediction = max(user_predictions, key=lambda x: x.get("prediction_id", ""))
    return latest_prediction

# Nudge endpoints
@app.post("/nudges/generate", status_code=201)
async def generate_user_nudges(user_id: str):
    """Generate nudges for a user."""
    nudges = generate_nudges(user_id)
    return {"nudges": [nudge.dict() for nudge in nudges], "count": len(nudges)}

@app.get("/nudges/{user_id}")
async def get_user_nudges(user_id: str):
    """Get all nudges for a user."""
    user_nudges = [n for n in nudges_db.values() if n["user_id"] == user_id]
    return {"nudges": user_nudges, "count": len(user_nudges)}

# Demo data endpoint
@app.post("/demo/setup")
async def setup_demo_data():
    """Set up demo data for testing."""
    # Create demo user
    demo_user = User(
        user_id="demo_user_123",
        phone_number="+1234567890",
        name="Demo User",
        income_schedule="irregular",
        risk_tolerance="conservative",
        auto_actions_enabled=True
    )
    users_db[demo_user.user_id] = demo_user.dict()
    
    # Create demo transactions
    demo_transactions = [
        Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id="demo_user_123",
            amount=5000,
            transaction_type="income",
            category="gig_income",
            description="Freelance project payment",
            transaction_date=datetime.utcnow().isoformat()
        ),
        Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id="demo_user_123",
            amount=1200,
            transaction_type="expense",
            category="groceries",
            description="Weekly groceries",
            transaction_date=(datetime.utcnow() - timedelta(days=1)).isoformat()
        ),
        Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id="demo_user_123",
            amount=300,
            transaction_type="expense",
            category="transport",
            description="Uber rides",
            transaction_date=(datetime.utcnow() - timedelta(days=2)).isoformat()
        ),
        Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id="demo_user_123",
            amount=3500,
            transaction_type="income",
            category="gig_income",
            description="Weekend gig payment",
            transaction_date=(datetime.utcnow() - timedelta(days=3)).isoformat()
        ),
        Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id="demo_user_123",
            amount=800,
            transaction_type="expense",
            category="entertainment",
            description="Movie tickets and dinner",
            transaction_date=(datetime.utcnow() - timedelta(days=4)).isoformat()
        )
    ]
    
    for transaction in demo_transactions:
        transactions_db[transaction.transaction_id] = transaction.dict()
    
    return {
        "message": "Demo data setup complete",
        "user_id": "demo_user_123",
        "transactions_created": len(demo_transactions),
        "current_balance": calculate_balance("demo_user_123")
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Financial Agent Test Server...")
    print("📱 Access the API at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Demo Setup: POST http://localhost:8000/demo/setup")
    uvicorn.run(app, host="0.0.0.0", port=8000)
