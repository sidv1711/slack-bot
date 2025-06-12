"""Base interface for Slack command handlers."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..types import SlackCommand, SlackResponse
from ..client import SlackClient

class BaseCommandHandler(ABC):
    """Base class for all command handlers."""
    
    def __init__(self, slack_client: SlackClient):
        """Initialize the handler.
        
        Args:
            slack_client (SlackClient): The Slack client for API calls
        """
        self.slack_client = slack_client
    
    @abstractmethod
    async def handle(self, command_data: SlackCommand) -> SlackResponse:
        """Handle the command.
        
        Args:
            command_data (SlackCommand): The command data from Slack
            
        Returns:
            SlackResponse: The response to send back to Slack
        """
        pass 