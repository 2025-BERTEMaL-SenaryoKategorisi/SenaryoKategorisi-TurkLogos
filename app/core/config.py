"""
Configuration settings for TürkLogos Agent
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://postgres:4Lt0g@localhost:5433/turklogos_db"
    redis_url: str = "redis://localhost:6379"
    
    # Redis connection details for enhanced auth
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # API Keys
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App Settings
    debug: bool = True
    environment: str = "development"
    log_level: str = "INFO"
    
    # Agent Settings
    max_conversation_length: int = 50
    default_response_timeout: int = 30
    max_iterations: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()