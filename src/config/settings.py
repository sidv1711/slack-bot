"""Application settings and configuration."""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

class Settings(BaseSettings):
    """Application settings."""
    
    # Development mode
    development_mode: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: Optional[str] = None
    slack_client_id: str
    slack_client_secret: str
    slack_oauth_redirect_uri: str
    
    # PropelAuth
    propelauth_api_key: str
    propelauth_url: str
    propelauth_verifier_key: Optional[str] = None
    propelauth_redirect_uri: str
    propelauth_client_id: str
    propelauth_client_secret: str
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Default to cost-effective model
    
    # AI Microservice
    ai_service_url: str = "http://localhost:8001"  # URL for the AI microservice
    ai_service_enabled: bool = True  # Whether to use microservice or direct services
    
    # Cognisim Backend (for test reports)
    cognisim_api_key: Optional[str] = None
    cognisim_base_url: str = "https://backend-staging.cognisim.io"
    
    # Application
    app_name: str = "slack-bot"
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
        extra="allow"
    )
    
    def __init__(self, **kwargs):
        """Initialize settings with validation."""
        super().__init__(**kwargs)
        
        # Log basic initialization info
        logger.info(f"Initialized settings for {self.environment} environment")
        logger.debug(f"Development mode: {self.development_mode}")
        logger.debug(f"Log level: {self.log_level}")
        
        # Validate required settings for production
        if not self.development_mode:
            self._validate_production_settings()
    
    def _validate_production_settings(self):
        """Validate required settings for production mode."""
        required_settings = [
            self.propelauth_url,
            self.propelauth_api_key,
            self.propelauth_redirect_uri,
            self.supabase_url,
            self.supabase_key,
            self.supabase_service_role_key
        ]
        
        # Only require OpenAI key if AI services are enabled
        if self.ai_service_enabled and not self.openai_api_key:
            required_settings.append(self.openai_api_key)
        
        if not all(required_settings):
            missing = []
            if not self.propelauth_url: missing.append("propelauth_url")
            if not self.propelauth_api_key: missing.append("propelauth_api_key") 
            if not self.propelauth_redirect_uri: missing.append("propelauth_redirect_uri")
            if not self.supabase_url: missing.append("supabase_url")
            if not self.supabase_key: missing.append("supabase_key")
            if not self.supabase_service_role_key: missing.append("supabase_service_role_key")
            if self.ai_service_enabled and not self.openai_api_key: missing.append("openai_api_key")
            
            raise ValueError(
                f"Missing required settings for production mode: {', '.join(missing)}"
            )
        
        # Validate URLs
        urls_to_validate = [
            self.propelauth_url,
            self.propelauth_redirect_uri,
            self.slack_oauth_redirect_uri,
            self.supabase_url
        ]
        
        for url in urls_to_validate:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL format: {url}")
                    
    def __hash__(self):
        """Make Settings hashable by using a tuple of its values."""
        return hash((
            self.development_mode,
            self.log_level,
            self.host,
            self.port,
            self.slack_bot_token,
            self.slack_signing_secret,
            self.slack_app_token,
            self.slack_client_id,
            self.slack_client_secret,
            self.slack_oauth_redirect_uri,
            self.propelauth_api_key,
            self.propelauth_url,
            self.propelauth_verifier_key,
            self.propelauth_redirect_uri,
            self.propelauth_client_id,
            self.propelauth_client_secret,
            self.supabase_url,
            self.supabase_key,
            self.supabase_service_role_key,
            self.openai_api_key,
            self.openai_model,
            self.ai_service_url,
            self.ai_service_enabled,
            self.cognisim_api_key,
            self.cognisim_base_url,
            self.app_name,
            self.environment
        ))
        
    def __eq__(self, other):
        """Required for hashable objects."""
        if not isinstance(other, Settings):
            return False
        return hash(self) == hash(other)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 