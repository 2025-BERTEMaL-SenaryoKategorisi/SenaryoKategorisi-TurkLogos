"""
Configuration settings for TürkLogos Agent
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
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
    
    # LLM Settings - GROQ FIRST for speed!
    llm_provider: str = "groq"  # "groq" for fast testing, "ollama" for local (disabled)
    groq_api_key: Optional[str] = None  # Set via GROQ_API_KEY env var
    groq_model: str = "llama3-8b-8192"  # Fast Groq model
    
    # Ollama settings (disabled for now - too slow)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
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
    
    # TEKNOFEST 2025 Specific Settings
    competition_mode: bool = True
    demo_data_enabled: bool = True
    collect_metrics: bool = True
    metrics_export_interval: int = 300
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields that might be in env file
    )

settings = Settings()