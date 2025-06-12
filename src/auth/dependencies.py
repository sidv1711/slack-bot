"""Dependency injection for auth components."""
from functools import lru_cache
from fastapi import Depends
from .user_store import UserMappingStore, MemoryUserMappingStore
from .supabase_store import SupabaseUserMappingStore
from ..config.settings import get_settings, Settings
from ..bot.client import SlackClient
from .mapping_service import UserMappingService

@lru_cache()
def get_user_mapping_store(settings: Settings = Depends(get_settings)) -> UserMappingStore:
    """Get the appropriate UserMappingStore implementation based on environment."""
    if settings.development_mode:
        return MemoryUserMappingStore()
    return SupabaseUserMappingStore(settings)

def get_slack_client(settings: Settings = Depends(get_settings)) -> SlackClient:
    """Get an instance of the SlackClient with the bot token from settings."""
    return SlackClient(bot_token=settings.slack_bot_token)

def get_user_mapping_service(
    store: UserMappingStore = Depends(get_user_mapping_store),
    slack_client: SlackClient = Depends(get_slack_client)
) -> UserMappingService:
    """Get an instance of the UserMappingService."""
    return UserMappingService(store=store, slack_client=slack_client) 