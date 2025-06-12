"""Slack middleware for request verification."""
from fastapi import Request
from loguru import logger

from ..config.settings import get_settings

async def verify_slack_request(request: Request) -> bool:
    """Verify that the request came from Slack."""
    settings = get_settings()
    if not settings.slack_bot_token:
        logger.info("Skipping Slack verification in development mode")
        return True
        
    # We'll implement proper verification later
    logger.warning("Production mode verification not yet implemented")
    return True