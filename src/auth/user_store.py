"""Storage for user mapping between Slack and PropelAuth."""
from typing import Optional, Dict, Protocol
from datetime import datetime
from loguru import logger
from ..models.user_mapping import UserMapping

class UserMappingStore(Protocol):
    """Protocol for user mapping storage."""
    
    async def save_mapping(self, mapping: UserMapping) -> None:
        """Save a user mapping."""
        ...
    
    async def get_by_slack_id(self, slack_user_id: str, team_id: str) -> Optional[UserMapping]:
        """Get mapping by Slack user ID."""
        ...
    
    async def get_by_propelauth_id(self, propelauth_user_id: str) -> Optional[UserMapping]:
        """Get mapping by PropelAuth user ID."""
        ...
    
    async def get_by_email(self, email: str) -> Optional[UserMapping]:
        """Get mapping by email (either Slack or PropelAuth)."""
        ...

class MemoryUserMappingStore(UserMappingStore):
    """In-memory implementation of UserMappingStore.
    
    Note: This is for development/testing only. Use a proper database in production.
    """
    
    def __init__(self):
        """Initialize the store."""
        self._mappings: Dict[str, UserMapping] = {}  # key: f"{team_id}:{slack_user_id}"
        self._propelauth_index: Dict[str, str] = {}  # propelauth_id -> mapping_key
        self._email_index: Dict[str, str] = {}  # email -> mapping_key
    
    async def save_mapping(self, mapping: UserMapping) -> None:
        """Save a user mapping."""
        key = f"{mapping.slack_team_id}:{mapping.slack_user_id}"
        mapping.updated_at = datetime.utcnow()
        
        # Store the mapping
        self._mappings[key] = mapping
        
        # Update indices
        self._propelauth_index[mapping.propelauth_user_id] = key
        self._email_index[mapping.propelauth_email] = key
        if mapping.slack_email:
            self._email_index[mapping.slack_email] = key
            
        logger.info(f"Saved user mapping for Slack user {mapping.slack_user_id}")
    
    async def get_by_slack_id(self, slack_user_id: str, team_id: str) -> Optional[UserMapping]:
        """Get mapping by Slack user ID."""
        key = f"{team_id}:{slack_user_id}"
        mapping = self._mappings.get(key)
        if mapping:
            logger.info(f"Found mapping for Slack user {slack_user_id}")
        else:
            logger.debug(f"No mapping found for Slack user {slack_user_id}")
        return mapping
    
    async def get_by_propelauth_id(self, propelauth_user_id: str) -> Optional[UserMapping]:
        """Get mapping by PropelAuth user ID."""
        key = self._propelauth_index.get(propelauth_user_id)
        if not key:
            logger.debug(f"No mapping found for PropelAuth user {propelauth_user_id}")
            return None
        
        mapping = self._mappings.get(key)
        if mapping:
            logger.info(f"Found mapping for PropelAuth user {propelauth_user_id}")
        return mapping
    
    async def get_by_email(self, email: str) -> Optional[UserMapping]:
        """Get mapping by email (either Slack or PropelAuth)."""
        key = self._email_index.get(email)
        if not key:
            logger.debug(f"No mapping found for email {email}")
            return None
        
        mapping = self._mappings.get(key)
        if mapping:
            logger.info(f"Found mapping for email {email}")
        return mapping 