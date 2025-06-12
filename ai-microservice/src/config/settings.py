"""Configuration settings for the AI Microservice."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """AI Microservice configuration settings."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # Supabase Configuration (for potential database access)
    supabase_url: str = ""
    supabase_key: str = ""
    
    # AI Service Configuration
    default_ai_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Service Configuration
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "production"
    
    # Allow extra fields from environment
    model_config = {"extra": "allow", "env_file": ".env"}


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None 