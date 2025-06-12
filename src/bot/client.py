"""Slack API client implementation."""
from typing import Optional, Dict, Any
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from loguru import logger

class SlackClient:
    """Slack API client wrapper.
    
    This class provides a wrapper around the Slack SDK AsyncWebClient,
    handling common operations and error cases.
    """
    
    def __init__(self, bot_token: str):
        """Initialize the Slack client.
        
        Args:
            bot_token (str): The Slack bot user token starting with xoxb-
        """
        self.client = AsyncWebClient(token=bot_token)
        
    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[list] = None
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel.
        
        Args:
            channel (str): The channel ID to send the message to
            text (str): The message text
            thread_ts (Optional[str]): Thread timestamp to reply to
            blocks (Optional[list]): Slack Block Kit blocks for rich formatting
            
        Returns:
            Dict[str, Any]: The response from the Slack API
            
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            if blocks:
                kwargs["blocks"] = blocks
                
            response = await self.client.chat_postMessage(**kwargs)
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Error sending message: {e.response['error']}")
            raise
            
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[list] = None
    ) -> Dict[str, Any]:
        """Update an existing message in a Slack channel.
        
        Args:
            channel (str): The channel ID where the message is
            ts (str): The timestamp of the message to update
            text (str): The new message text
            blocks (Optional[list]): Slack Block Kit blocks for rich formatting
            
        Returns:
            Dict[str, Any]: The response from the Slack API
            
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            kwargs = {
                "channel": channel,
                "ts": ts,
                "text": text
            }
            if blocks:
                kwargs["blocks"] = blocks
                
            response = await self.client.chat_update(**kwargs)
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")
            raise
            
    async def send_ephemeral_message(
        self,
        user_id: str,
        channel: str,
        text: str,
        blocks: Optional[list] = None
    ) -> Dict[str, Any]:
        """Send an ephemeral message to a specific user in a channel.
        
        Args:
            user_id (str): The user ID to send the ephemeral message to
            channel (str): The channel ID where the message should appear
            text (str): The message text
            blocks (Optional[list]): Slack Block Kit blocks for rich formatting
            
        Returns:
            Dict[str, Any]: The response from the Slack API
            
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            kwargs = {
                "channel": channel,
                "user": user_id,
                "text": text
            }
            if blocks:
                kwargs["blocks"] = blocks
                
            response = await self.client.chat_postEphemeral(**kwargs)
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Error sending ephemeral message: {e.response['error']}")
            raise
            
    async def react_to_message(
        self,
        channel: str,
        timestamp: str,
        reaction: str
    ) -> Dict[str, Any]:
        """Add a reaction to a message.
        
        Args:
            channel (str): Channel ID where the message is
            timestamp (str): Timestamp of the message to react to
            reaction (str): Name of the emoji reaction
            
        Returns:
            Dict[str, Any]: The response from the Slack API
            
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            response = await self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=reaction
            )
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Error adding reaction: {e.response['error']}")
            raise
            
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a Slack user.
        
        Args:
            user_id (str): The Slack user ID
            
        Returns:
            Dict[str, Any]: User information from the Slack API
            
        Raises:
            SlackApiError: If the API call fails
        """
        try:
            response = await self.client.users_info(user=user_id)
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e.response['error']}")
            raise 