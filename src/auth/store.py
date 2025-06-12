"""Storage implementations for Slack OAuth data."""
from typing import Optional, Dict
import time
import secrets
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.models.installation import Installation
from loguru import logger

class MemoryInstallationStore(InstallationStore):
    """In-memory implementation of InstallationStore.
    
    Note: This is for development/testing only. Use a proper database in production.
    """
    
    def __init__(self):
        """Initialize the store."""
        self._installations: Dict[str, Installation] = {}
        
    async def save(self, installation: Installation) -> None:
        """Save an installation."""
        key = f"{installation.enterprise_id}:{installation.team_id}"
        self._installations[key] = installation
        logger.info(f"Saved installation for {key}")
        
    async def find_installation(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False
    ) -> Optional[Installation]:
        """Find an installation by enterprise/team ID."""
        key = f"{enterprise_id}:{team_id}"
        installation = self._installations.get(key)
        if installation:
            logger.info(f"Found installation for {key}")
        else:
            logger.warning(f"No installation found for {key}")
        return installation

class StateStore:
    """Simple in-memory state store for OAuth flow.
    
    Note: This is for development/testing only. Use a proper database in production.
    """
    
    def __init__(self):
        """Initialize the store."""
        self._states: Dict[str, int] = {}
        
    def issue(self) -> str:
        """Issue a new state parameter."""
        state = secrets.token_urlsafe(32)  # Generate a secure random state
        self._states[state] = int(time.time())
        return state
        
    def consume(self, state: str) -> bool:
        """Consume and validate a state parameter."""
        if state not in self._states:
            return False
            
        # Remove the state to prevent replay attacks
        timestamp = self._states.pop(state)
        
        # Check if state is expired (10 minutes)
        now = int(time.time())
        return (now - timestamp) <= 600  # 10 minutes in seconds 