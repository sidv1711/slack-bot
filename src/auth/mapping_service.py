"""Service for managing user mapping between Slack and PropelAuth."""
from typing import Optional
from loguru import logger
from datetime import datetime
from .user_store import UserMappingStore
from ..models.user_mapping import UserMapping
from ..bot.client import SlackClient
from ..utils.logging import log_operation, log_user_action, log_error_with_context
from propelauth_fastapi import User as PropelAuthUser

class UserMappingService:
    """Service for managing user mappings."""
    
    def __init__(self, store: UserMappingStore, slack_client: SlackClient):
        """Initialize the service."""
        self._store = store
        self._slack_client = slack_client
        logger.info("UserMappingService initialized")
    
    @log_operation("user mapping creation")
    async def get_or_create_mapping(
        self,
        slack_user_id: str,
        team_id: str,
        propelauth_user: PropelAuthUser
    ) -> UserMapping:
        """Get existing mapping or create a new one."""
        log_user_action(slack_user_id, "requesting user mapping", f"PropelAuth user: {propelauth_user.user_id}")
        
        # Try to find existing mapping
        mapping = await self._store.get_by_slack_id(slack_user_id, team_id)
        if mapping:
            logger.info(f"Found existing mapping for user {slack_user_id}")
            # Update if PropelAuth info changed
            if (mapping.propelauth_user_id != propelauth_user.user_id or
                mapping.propelauth_email != propelauth_user.email):
                logger.info("Updating mapping with new PropelAuth info")
                mapping.propelauth_user_id = propelauth_user.user_id
                mapping.propelauth_email = propelauth_user.email
                mapping.updated_at = datetime.utcnow()
                await self._store.save_mapping(mapping)
            return mapping
            
        # Get Slack user info
        slack_email = None
        try:
            slack_user_info = await self._slack_client.get_user_info(slack_user_id)
            slack_email = slack_user_info.get("user", {}).get("email")
            logger.debug(f"Retrieved Slack email: {slack_email}")
        except Exception as e:
            logger.warning(f"Could not get Slack user info: {e}")
            
        # Create new mapping
        mapping = UserMapping(
            slack_user_id=slack_user_id,
            propelauth_user_id=propelauth_user.user_id,
            slack_team_id=team_id,
            slack_email=slack_email,
            propelauth_email=propelauth_user.email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self._store.save_mapping(mapping)
        log_user_action(slack_user_id, "created user mapping", f"PropelAuth: {propelauth_user.user_id}")
        
        return mapping
    
    async def get_propelauth_user_for_slack(
        self,
        slack_user_id: str,
        team_id: str
    ) -> Optional[str]:
        """Get PropelAuth user ID for a Slack user."""
        try:
            mapping = await self._store.get_by_slack_id(slack_user_id, team_id)
            if mapping:
                logger.debug(f"Found PropelAuth user {mapping.propelauth_user_id} for Slack user {slack_user_id}")
                return mapping.propelauth_user_id
            logger.debug(f"No PropelAuth mapping found for Slack user {slack_user_id}")
            return None
        except Exception as e:
            log_error_with_context(e, {
                "slack_user_id": slack_user_id,
                "team_id": team_id,
                "operation": "get_propelauth_user_for_slack"
            })
            raise
    
    async def get_slack_user_for_propelauth(
        self,
        propelauth_user_id: str
    ) -> Optional[tuple[str, str]]:
        """Get Slack user ID and team ID for a PropelAuth user."""
        try:
            mapping = await self._store.get_by_propelauth_id(propelauth_user_id)
            if mapping:
                logger.debug(f"Found Slack user {mapping.slack_user_id} for PropelAuth user {propelauth_user_id}")
                return (mapping.slack_user_id, mapping.slack_team_id)
            logger.debug(f"No Slack mapping found for PropelAuth user {propelauth_user_id}")
            return None
        except Exception as e:
            log_error_with_context(e, {
                "propelauth_user_id": propelauth_user_id,
                "operation": "get_slack_user_for_propelauth"
            })
            raise
    
    @log_operation("smart mapping strategy")
    async def smart_get_or_create_mapping(
        self, 
        slack_user_id: str, 
        team_id: str,
        propelauth_user: Optional[PropelAuthUser] = None
    ) -> Optional[UserMapping]:
        """
        Smart mapping strategy:
        1. Check for existing mapping
        2. Try automatic email-based mapping (if user consents)
        3. Fall back to manual connection flow
        """
        # 1. Check for existing mapping
        existing = await self._store.get_by_slack_id(slack_user_id, team_id)
        if existing:
            logger.info(f"Found existing mapping for user {slack_user_id}")
            return existing
        
        # 2. Try automatic email mapping (only if we have PropelAuth user)
        if propelauth_user:
            logger.info("Attempting automatic email-based mapping")
            try:
                slack_user_info = await self._slack_client.get_user_info(slack_user_id)
                if slack_user_info and slack_user_info.get("email"):
                    slack_email = slack_user_info["email"]
                    
                    # Check if emails match
                    if slack_email.lower() == propelauth_user.email.lower():
                        logger.info(f"Email match found: {slack_email}")
                        
                        mapping = UserMapping(
                            slack_user_id=slack_user_id,
                            propelauth_user_id=propelauth_user.user_id,
                            slack_team_id=team_id,
                            slack_email=slack_email,
                            propelauth_email=propelauth_user.email,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        await self._store.save_mapping(mapping)
                        log_user_action(slack_user_id, "auto-mapped via email", propelauth_user.email)
                        return mapping
                    else:
                        logger.info(f"Email mismatch: Slack={slack_email}, PropelAuth={propelauth_user.email}")
                        
            except Exception as e:
                logger.warning(f"Auto-mapping failed, will require manual connection: {e}")
        
        # 3. No automatic mapping possible
        logger.info("No automatic mapping possible - manual connection required")
        return None 