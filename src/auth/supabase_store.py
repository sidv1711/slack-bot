"""Supabase implementations of storage interfaces."""
from typing import Optional
from datetime import datetime
from loguru import logger
from supabase import create_client, Client
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.models.installation import Installation
from .user_store import UserMappingStore
from ..models.user_mapping import UserMapping
from ..config.settings import Settings
from ..utils.logging import log_database_operation, log_error_with_context

class SupabaseInstallationStore(InstallationStore):
    """Supabase implementation of InstallationStore."""
    
    def __init__(self, settings: Settings):
        """Initialize the store with Supabase client."""
        if not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for installation store")
            
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info("Initialized Supabase installation store")
    
    async def save(self, installation: Installation) -> None:
        """Save an installation to Supabase."""
        try:
            log_database_operation("slack_installations", "save", {"team_id": installation.team_id})
            
            installation_dict = {
                "app_id": installation.app_id,
                "enterprise_id": installation.enterprise_id,
                "team_id": installation.team_id,
                "bot_token": installation.bot_token,
                "bot_id": installation.bot_id,
                "bot_scopes": ",".join(installation.bot_scopes),
                "user_id": installation.user_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("slack_installations").upsert(
                installation_dict,
                on_conflict="team_id"
            ).execute()
            
            logger.info(f"Saved installation for team {installation.team_id}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            log_error_with_context(e, {"team_id": installation.team_id, "operation": "save_installation"})
            raise
    
    async def find_installation(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False
    ) -> Optional[Installation]:
        """Find an installation by enterprise/team ID from Supabase."""
        try:
            log_database_operation("slack_installations", "find", {"team_id": team_id})
            
            query = self.supabase.table("slack_installations").select("*")
            if team_id:
                query = query.eq("team_id", team_id)
            if enterprise_id:
                query = query.eq("enterprise_id", enterprise_id)
            
            result = query.execute()
            
            if not result.data:
                logger.debug(f"No installation found for team {team_id}")
                return None
            
            data = result.data[0]
            installation = Installation(
                app_id=data["app_id"],
                enterprise_id=data.get("enterprise_id"),
                team_id=data["team_id"],
                bot_token=data["bot_token"],
                bot_id=data["bot_id"],
                bot_scopes=data["bot_scopes"].split(","),
                user_id=data["user_id"]
            )
            
            logger.info(f"Found installation for team {team_id}")
            return installation
            
        except Exception as e:
            log_error_with_context(e, {"team_id": team_id, "operation": "find_installation"})
            raise

class SupabaseUserMappingStore(UserMappingStore):
    """Supabase implementation of UserMappingStore."""
    
    def __init__(self, settings: Settings):
        """Initialize the store with Supabase client."""
        if not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for user mapping store")
            
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info("Initialized Supabase user mapping store")
        
        # Test connection
        try:
            self.supabase.table("user_mappings").select("*").limit(1).execute()
            logger.debug("Successfully connected to user_mappings table")
        except Exception as e:
            logger.error(f"Error connecting to user_mappings table: {e}")
            raise
    
    async def save_mapping(self, mapping: UserMapping) -> None:
        """Save a user mapping to Supabase."""
        try:
            log_database_operation("user_mappings", "save", {
                "slack_user_id": mapping.slack_user_id,
                "propelauth_user_id": mapping.propelauth_user_id
            })
            
            # Convert to dict and handle datetime
            mapping_dict = mapping.model_dump(exclude={'id'})
            mapping_dict["created_at"] = mapping_dict["created_at"].isoformat() if mapping_dict.get("created_at") else datetime.utcnow().isoformat()
            mapping_dict["updated_at"] = datetime.utcnow().isoformat()
            
            # Try insert first, then update if conflict
            try:
                result = self.supabase.table("user_mappings").insert(mapping_dict).execute()
                logger.info(f"Created new user mapping: {mapping.slack_user_id} -> {mapping.propelauth_user_id}")
                return result.data[0]
            except Exception:
                # Update existing record on conflict
                result = self.supabase.table("user_mappings").update({
                    "propelauth_user_id": mapping_dict["propelauth_user_id"],
                    "slack_email": mapping_dict.get("slack_email"),
                    "propelauth_email": mapping_dict["propelauth_email"],
                    "updated_at": mapping_dict["updated_at"]
                }).match({
                    "slack_user_id": mapping_dict["slack_user_id"],
                    "slack_team_id": mapping_dict["slack_team_id"]
                }).execute()
                
                if not result.data:
                    raise Exception("No data returned from update operation")
                    
                logger.info(f"Updated existing user mapping: {mapping.slack_user_id} -> {mapping.propelauth_user_id}")
                return result.data[0]
            
        except Exception as e:
            log_error_with_context(e, {
                "slack_user_id": mapping.slack_user_id,
                "propelauth_user_id": mapping.propelauth_user_id,
                "operation": "save_mapping"
            })
            raise
    
    async def get_by_slack_id(self, slack_user_id: str, team_id: str) -> Optional[UserMapping]:
        """Get mapping by Slack user ID from Supabase."""
        try:
            log_database_operation("user_mappings", "get_by_slack_id", {
                "slack_user_id": slack_user_id,
                "team_id": team_id
            })
            
            result = self.supabase.table("user_mappings").select("*").match({
                "slack_user_id": slack_user_id,
                "slack_team_id": team_id
            }).execute()
            
            if result.data:
                logger.debug(f"Found mapping for Slack user {slack_user_id}")
                return UserMapping(**result.data[0])
            
            logger.debug(f"No mapping found for Slack user {slack_user_id}")
            return None
            
        except Exception as e:
            log_error_with_context(e, {
                "slack_user_id": slack_user_id,
                "team_id": team_id,
                "operation": "get_by_slack_id"
            })
            raise
    
    async def get_by_propelauth_id(self, propelauth_user_id: str) -> Optional[UserMapping]:
        """Get mapping by PropelAuth user ID from Supabase."""
        try:
            log_database_operation("user_mappings", "get_by_propelauth_id", {
                "propelauth_user_id": propelauth_user_id
            })
            
            result = self.supabase.table("user_mappings").select("*").match({
                "propelauth_user_id": propelauth_user_id
            }).execute()
            
            if result.data:
                logger.debug(f"Found mapping for PropelAuth user {propelauth_user_id}")
                return UserMapping(**result.data[0])
            
            logger.debug(f"No mapping found for PropelAuth user {propelauth_user_id}")
            return None
            
        except Exception as e:
            log_error_with_context(e, {
                "propelauth_user_id": propelauth_user_id,
                "operation": "get_by_propelauth_id"
            })
            raise
    
    async def get_by_email(self, email: str) -> Optional[UserMapping]:
        """Get mapping by email from Supabase."""
        try:
            log_database_operation("user_mappings", "get_by_email", {"email": email})
            
            result = self.supabase.table("user_mappings").select("*").or_(
                f"slack_email.eq.{email},propelauth_email.eq.{email}"
            ).execute()
            
            if result.data:
                logger.debug(f"Found mapping for email {email}")
                return UserMapping(**result.data[0])
            
            logger.debug(f"No mapping found for email {email}")
            return None
            
        except Exception as e:
            log_error_with_context(e, {"email": email, "operation": "get_by_email"})
            raise 