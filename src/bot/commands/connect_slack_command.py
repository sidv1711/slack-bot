"""Handler for the /connect-slack command."""
from typing import Dict, Any
from loguru import logger
from ..types import SlackCommand, SlackResponse
from ..client import SlackClient
from .base import BaseCommandHandler

class ConnectSlackCommandHandler(BaseCommandHandler):
    """Handler for the /connect-slack command."""
    
    def __init__(self, slack_client):
        super().__init__(slack_client)
        self.command_name = "connect-slack"
    
    async def handle(self, command_data: dict) -> dict:
        """Handle the connect-slack command."""
        user_id = command_data.get("user_id")
        team_id = command_data.get("team_id")
        channel_id = command_data.get("channel_id")
        user_name = command_data.get("user_name", "User")
        text = command_data.get("text", "").strip().lower()
        
        logger.info(f"Connect command received: user={user_id}, team={team_id}, channel={channel_id}, mode={text}")
        
        # Generate the connect URL
        connect_url = f"https://api.example.com/auth/connect-slack?slack_user_id={user_id}&team_id={team_id}"
        
        # Send a properly formatted message to the channel
        message_text = f"🔗 **Account Connection for {user_name}**\n\nClick the link below to connect your Slack account with PropelAuth:\n\n👉 {connect_url}\n\n*This will allow you to access personalized features and reports.*"
        
        await self.slack_client.send_message(
            channel=channel_id,
            text=message_text
        )
        
        return {
            "ok": True,
            "message": "Connection link sent successfully",
            "received": command_data,
            "error": None
        } 