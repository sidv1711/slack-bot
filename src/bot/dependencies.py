"""Dependency injection container for the application."""
from functools import lru_cache
from typing import Dict, Any, Optional

from fastapi import Depends, Request
from .services import SlackService
from ..config.settings import get_settings, Settings
from .client import SlackClient
from ..auth.store import MemoryInstallationStore
from ..auth.supabase_store import SupabaseInstallationStore

# Global SlackService instance for singleton pattern
_slack_service_instance: Optional[SlackService] = None

@lru_cache()
def get_installation_store():
    """Get a cached instance of the installation store."""
    settings = get_settings()
    return SupabaseInstallationStore(settings) if not settings.development_mode else MemoryInstallationStore()

async def extract_team_id_from_request(request: Request) -> Optional[str]:
    """Extract team_id from request, handling both form data and JSON."""
    if request.method != "POST":
        return None
        
    # Check if we already cached the team_id in request state
    if hasattr(request.state, "team_id"):
        return request.state.team_id
        
    team_id = None
    try:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            team_id = form_data.get("team_id")
        elif "application/json" in content_type:
            body = await request.json()
            team_id = body.get("team_id")
    except Exception:
        pass
    
    # Cache the team_id in request state
    request.state.team_id = team_id
    return team_id

async def get_slack_client(
    request: Request,
    settings: Settings = Depends(get_settings),
    installation_store = Depends(get_installation_store)
) -> SlackClient:
    """Get a Slack client for the current team."""
    if settings.development_mode:
        return SlackClient("<SLACK_TOKEN>")
        
    team_id = await extract_team_id_from_request(request)
    if not team_id:
        raise ValueError("Could not determine team_id from request")
        
    # Get installation for this team
    installation = await installation_store.find_installation(
        enterprise_id=None,
        team_id=team_id
    )
    
    if not installation:
        raise ValueError(f"No installation found for team {team_id}")
        
    return SlackClient(installation.bot_token)

def get_slack_service(
    settings: Settings = Depends(get_settings),
    slack_client: SlackClient = Depends(get_slack_client)
) -> SlackService:
    """Get a singleton instance of the Slack service for event deduplication."""
    global _slack_service_instance
    
    # Create singleton instance if it doesn't exist
    if _slack_service_instance is None:
        _slack_service_instance = SlackService(
            development_mode=settings.development_mode,
            slack_client=slack_client if not settings.development_mode else None
        )
    
    # Update the slack_client for the current request
    if not settings.development_mode:
        _slack_service_instance.slack_client = slack_client
    
    return _slack_service_instance

class Dependencies:
    """Container for application dependencies."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._slack_service: SlackService | None = None
    
    @property
    def slack_service(self) -> SlackService:
        """Get the SlackService instance."""
        if self._slack_service is None:
            self._slack_service = SlackService(development_mode=self.settings.development_mode)
        return self._slack_service

@lru_cache()
def get_dependencies(settings: Settings = Depends(get_settings)) -> Dependencies:
    """Get or create a Dependencies instance."""
    return Dependencies(settings) 