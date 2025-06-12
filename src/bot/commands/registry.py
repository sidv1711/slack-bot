"""Command registry for managing Slack command handlers."""
from typing import Dict, Type
from .hello_command import HelloCommandHandler
from .connect_slack_command import ConnectSlackCommandHandler
from .ai_command import AICommandHandler
from .test_executions_command import TestExecutionsCommandHandler
from ..client import SlackClient

class CommandRegistry:
    """Registry for Slack command handlers."""
    
    def __init__(self, slack_client: SlackClient):
        """Initialize the registry.
        
        Args:
            slack_client (SlackClient): The Slack client for API calls
        """
        self.slack_client = slack_client
        self._handlers = {
            "/hello": HelloCommandHandler(slack_client),
            "/connect-slack": ConnectSlackCommandHandler(slack_client),
            "/ai": AICommandHandler(slack_client),
            "/test-executions": TestExecutionsCommandHandler(slack_client)
        }
    
    def get_handler(self, command: str):
        """Get the handler for a command.
        
        Args:
            command (str): The command to get a handler for
            
        Returns:
            Optional[Any]: The handler for the command, or None if not found
        """
        return self._handlers.get(command)
    
    def register_handler(self, command: str, handler_class: Type):
        """Register a new command handler.
        
        Args:
            command (str): The command to register a handler for
            handler_class (Type): The handler class to instantiate
        """
        self._handlers[command] = handler_class(self.slack_client) 