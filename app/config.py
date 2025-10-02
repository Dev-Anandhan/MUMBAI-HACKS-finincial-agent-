"""Configuration management for the financial agent."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = "postgresql://user:password@localhost/financial_agent"
    redis_url: str = "redis://localhost:6379"
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cursor_api_key: str = "key_27841618d8073dffdbe93dfef31ca1d0c647227c40d0b4ec68027794bab4f6dd"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App Settings
    debug: bool = True
    environment: str = "development"
    api_v1_str: str = "/api/v1"
    
    # Privacy & Security
    encryption_key: str = "your-encryption-key-change-in-production"
    data_retention_days: int = 90
    max_auto_action_amount: float = 500.0
    
    # Feature Flags
    enable_auto_actions: bool = True
    enable_voice_bot: bool = True
    enable_sms_gateway: bool = True
    
    # Model Settings
    cashflow_prediction_days: int = 30
    nudge_confidence_threshold: float = 0.7
    max_nudge_frequency_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()