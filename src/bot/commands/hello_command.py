"""Handler for the /hello command."""
from typing import Dict, Any
from loguru import logger
from ..types import SlackCommand, SlackResponse
from ..client import SlackClient
from .base import BaseCommandHandler

class HelloCommandHandler(BaseCommandHandler):
    """Handler for the /hello command."""
    
    async def handle(self, command_data: SlackCommand) -> SlackResponse:
        """Handle the /hello command.
        
        Args:
            command_data (SlackCommand): The command data from Slack
            
        Returns:
            SlackResponse: The response to send back to Slack
        """
        try:
            channel_id = command_data["channel_id"]
            user_id = command_data["user_id"]
            user_name = command_data["user_name"]
            text = command_data.get("text", "")
            
            # Get user info for a more personalized greeting
            try:
                user_info = await self.slack_client.get_user_info(user_id)
                display_name = user_info.get("user", {}).get("real_name") or user_name
            except Exception:
                display_name = user_name
            
            greeting = f"👋 Hello {display_name}!"
            if text:
                greeting += f" {text}"
            
            # Send the greeting
            await self.slack_client.send_message(
                channel=channel_id,
                text=greeting,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": greeting
                        }
                    }
                ]
            )
            
            return {
                "ok": True,
                "message": "Greeting sent successfully",
                "received": command_data,
                "error": None
            }
            
        except Exception as e:
            logger.exception("Error handling hello command")
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": command_data
            } 