"""Main FastAPI application for the Financial Agent."""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.database import get_database
from app.api.v1 import users, transactions, predictions, nudges, actions, pots
from app.services.cashflow_predictor import CashflowPredictor
from app.services.nudge_engine import NudgeEngine
from app.services.decision_engine import DecisionEngine


# Global service instances
cashflow_predictor = None
nudge_engine = None
decision_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global cashflow_predictor, nudge_engine, decision_engine
    
    # Startup
    print("🚀 Starting Financial Agent...")
    
    # Initialize ML services
    cashflow_predictor = CashflowPredictor()
    nudge_engine = NudgeEngine()
    decision_engine = DecisionEngine()
    
    print("✅ Financial Agent started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Financial Agent...")


# Create FastAPI app
app = FastAPI(
    title="Financial Agent API",
    description="Autonomous financial coaching agent for gig workers and informal sector employees",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # TODO: Implement JWT token validation
    # For now, return a mock user ID
    return {"user_id": "user_123", "phone_number": "+1234567890"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "financial-agent",
        "version": "1.0.0",
        "features": {
            "auto_actions": settings.enable_auto_actions,
            "voice_bot": settings.enable_voice_bot,
            "sms_gateway": settings.enable_sms_gateway
        }
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Financial Agent API",
        "description": "Autonomous financial coaching agent for gig workers",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include API routers
app.include_router(
    users.router,
    prefix=f"{settings.api_v1_str}/users",
    tags=["users"]
)

app.include_router(
    transactions.router,
    prefix=f"{settings.api_v1_str}/transactions",
    tags=["transactions"]
)

app.include_router(
    predictions.router,
    prefix=f"{settings.api_v1_str}/predictions",
    tags=["predictions"]
)

app.include_router(
    nudges.router,
    prefix=f"{settings.api_v1_str}/nudges",
    tags=["nudges"]
)

app.include_router(
    actions.router,
    prefix=f"{settings.api_v1_str}/actions",
    tags=["actions"]
)

app.include_router(
    pots.router,
    prefix=f"{settings.api_v1_str}/pots",
    tags=["savings-pots"]
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url)
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "path": str(request.url)
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
