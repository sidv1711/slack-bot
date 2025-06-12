"""Services for handling Slack interactions.

This module provides the core business logic for handling Slack events and commands.
It supports both development and production modes, with development mode providing
mock responses for testing and development purposes.
"""
from typing import Dict, Any, Optional, Union, Set
from loguru import logger
import time
from .types import SlackEvent, SlackCommand, SlackResponse
from .client import SlackClient
from .commands.registry import CommandRegistry
from ..services.ai_client_service import AIClientService
from ..services.database_service import DatabaseService

class SlackService:
    """Service class for handling Slack interactions.
    
    This class provides methods for processing Slack events and commands,
    with support for both development and production environments.
    
    Attributes:
        development_mode (bool): Whether the service is running in development mode.
            In development mode, real Slack API calls are mocked.
        slack_client (Optional[SlackClient]): Slack client for API calls
        ai_router (AIRouterService): AI router for intelligent responses
        _processed_events (Set[str]): Set of processed event IDs for deduplication
        _event_timestamps (Dict[str, float]): Timestamps of processed events for cleanup
    """
    
    def __init__(
        self,
        development_mode: bool = True,
        slack_client: Optional[SlackClient] = None
    ):
        """Initialize the SlackService.
        
        Args:
            development_mode (bool): Whether to run in development mode
            slack_client (Optional[SlackClient]): Slack client for API calls
        """
        self.development_mode = development_mode
        self._slack_client = slack_client
        
        if not development_mode and slack_client is None:
            raise ValueError("slack_client is required when not in development mode")
            
        self.command_registry = CommandRegistry(slack_client) if slack_client else None
        # Initialize AI router for intelligent responses
        self.ai_router = AIClientService()
        
        # Event deduplication tracking
        self._processed_events: Set[str] = set()
        self._event_timestamps: Dict[str, float] = {}
        
        logger.info("SlackService initialized with AI router and event deduplication")
    
    @property
    def slack_client(self) -> Optional[SlackClient]:
        """Get the current Slack client."""
        return self._slack_client
    
    @slack_client.setter
    def slack_client(self, client: Optional[SlackClient]) -> None:
        """Set the Slack client and update command registry."""
        self._slack_client = client
        if client:
            self.command_registry = CommandRegistry(client)
        else:
            self.command_registry = None
    
    def _is_duplicate_event(self, event_id: str, event_ts: str) -> bool:
        """Check if an event has already been processed to prevent duplicates.
        
        Args:
            event_id (str): Unique event ID from Slack
            event_ts (str): Event timestamp
            
        Returns:
            bool: True if this is a duplicate event
        """
        current_time = time.time()
        
        # Clean up old events (older than 5 minutes)
        cutoff_time = current_time - 300  # 5 minutes
        events_to_remove = [
            eid for eid, timestamp in self._event_timestamps.items()
            if timestamp < cutoff_time
        ]
        for eid in events_to_remove:
            self._processed_events.discard(eid)
            self._event_timestamps.pop(eid, None)
        
        # Create a unique identifier for this event
        event_key = f"{event_id}:{event_ts}"
        
        if event_key in self._processed_events:
            logger.warning(f"Duplicate event detected: {event_key}")
            return True
        
        # Mark this event as processed
        self._processed_events.add(event_key)
        self._event_timestamps[event_key] = current_time
        return False
    
    async def handle_event(self, event_data: Union[Dict[str, Any], None]) -> SlackResponse:
        """Handle incoming Slack events.
        
        Processes various types of Slack events including app_mention, message,
        and other event types defined in the Slack Events API.
        
        Args:
            event_data (Dict[str, Any] | None): The raw event data from Slack.
                Should contain at least 'type' and other event-specific fields.
        
        Returns:
            SlackResponse: A response indicating success/failure and any relevant messages.
            
        Raises:
            Exception: If there's an error processing the event.
        """
        try:
            if event_data is None:
                raise ValueError("Event data cannot be None")
            
            # Check for duplicate events (only in production mode)
            if not self.development_mode:
                event = event_data.get("event", {})
                event_id = event_data.get("event_id")
                event_ts = event.get("ts")
                
                if event_id and event_ts:
                    if self._is_duplicate_event(event_id, event_ts):
                        logger.info(f"Skipping duplicate event: {event_id}")
                        return {
                            "ok": True,
                            "message": "Duplicate event ignored",
                            "received": event_data,
                            "error": None
                        }
            
            if self.development_mode:
                logger.info(f"Development mode: Received event {event_data}")
                return {
                    "ok": True,
                    "message": "Event processed in development mode",
                    "received": event_data,
                    "error": None
                }
            
            # Production mode handling
            event = event_data.get("event", {})
            event_type = event.get("type")
            
            logger.info(f"Processing event type: {event_type}")
            
            if event_type == "app_mention":
                return await self._handle_mention(event)
            elif event_type == "message":
                return await self._handle_message(event)
            else:
                logger.warning(f"Unhandled event type: {event_type}")
                return {
                    "ok": True,
                    "message": f"Received unhandled event type: {event_type}",
                    "received": event_data,
                    "error": None
                }
                
        except Exception as e:
            logger.exception("Error handling Slack event")
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": event_data
            }
    
    async def handle_command(self, command_data: Union[SlackCommand, None]) -> SlackResponse:
        """Handle Slack slash commands.
        
        Processes slash commands sent from Slack, such as /hello or custom commands.
        
        Args:
            command_data (SlackCommand | None): The command data from Slack.
                Must include 'command', 'text', 'user_id', and other required fields.
        
        Returns:
            SlackResponse: A response indicating success/failure and any relevant messages.
            
        Raises:
            Exception: If there's an error processing the command.
        """
        try:
            if command_data is None:
                raise ValueError("Command data cannot be None")
            
            if self.development_mode:
                logger.info(f"Development mode: Received command {command_data}")
                return {
                    "ok": True,
                    "message": f"Command processed in development mode: {command_data['command']}",
                    "received": command_data,
                    "error": None
                }
            
            # Production mode handling
            command = command_data["command"]
            
            # Get the appropriate handler from the registry
            handler = self.command_registry.get_handler(command)
            if handler:
                return await handler.handle(command_data)
            
            return {
                "ok": False,
                "error": f"Unknown command: {command}",
                "message": None,
                "received": command_data
            }
            
        except Exception as e:
            logger.exception("Error handling Slack command")
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": command_data
            }
            
    async def _handle_mention(self, event: Dict[str, Any]) -> SlackResponse:
        """Handle app mention events with AI-powered responses."""
        try:
            channel = event["channel"]
            user = event["user"]
            text = event.get("text", "")
            ts = event.get("ts")
            
            logger.info(f"Processing mention in channel {channel} from user {user}")
            
            # Get user info
            user_info = await self.slack_client.get_user_info(user)
            user_name = user_info.get("user", {}).get("name", "User")
            
            # Extract the actual message text (remove the bot mention)
            # Slack mentions come as "<@U12345> your message here"
            import re
            clean_text = re.sub(r'<@[^>]+>\s*', '', text).strip()
            
            logger.info(f"Processing AI mention from {user_name}: {clean_text}")
            
            if not clean_text:
                # Show help message if no text provided
                help_text = self._get_ai_help_message()
                await self.slack_client.send_message(
                    channel=channel,
                    text=help_text,
                    thread_ts=ts
                )
                
                await self.slack_client.react_to_message(
                    channel=channel,
                    timestamp=ts,
                    reaction="wave"
                )
                
                return {
                    "ok": True,
                    "message": "AI help message sent for mention",
                    "received": event,
                    "error": None
                }
            
            # Send initial "thinking" message
            thinking_msg = await self.slack_client.send_message(
                channel=channel,
                text=f"🤖 *Processing your request:* _{clean_text}_\n⏳ Thinking...",
                thread_ts=ts
            )
            
            # Build context for AI router
            context = {
                "user_id": user,
                "user_name": user_name,
                "channel_id": channel,
                "platform": "slack",
                "interaction_type": "mention"
            }
            
            # Get AI response
            ai_result = await self.ai_router.process_request(
                user_input=clean_text,
                context=context
            )
            
            # Format response
            response_text = self._format_ai_response(ai_result, user_name)
            
            # Update the thinking message with the actual response
            if thinking_msg.get("ts"):
                await self.slack_client.update_message(
                    channel=channel,
                    ts=thinking_msg["ts"],
                    text=response_text
                )
            else:
                # Fallback: send new message
                await self.slack_client.send_message(
                    channel=channel,
                    text=response_text,
                    thread_ts=ts
                )
            
            # Add completion reaction
            await self.slack_client.react_to_message(
                channel=channel,
                timestamp=thinking_msg.get("ts") or ts,
                reaction="white_check_mark"
            )
            
            return {
                "ok": True,
                "message": "AI mention processed successfully",
                "received": event,
                "error": None
            }
            
        except Exception as e:
            logger.exception("Error handling mention")
            
            # Send error message to user
            try:
                error_text = f"❌ Sorry, I encountered an error processing your request:\n```{str(e)}```"
                await self.slack_client.send_message(
                    channel=event.get("channel"),
                    text=error_text,
                    thread_ts=event.get("ts")
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
            
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": event
            }
            
    async def _handle_message(self, event: Dict[str, Any]) -> SlackResponse:
        """Handle message events."""
        try:
            # Ignore messages from bots to prevent loops
            if event.get("bot_id"):
                return {
                    "ok": True,
                    "message": "Ignored bot message",
                    "received": event,
                    "error": None
                }
            
            # Check if this is a direct message
            channel_type = event.get("channel_type")
            channel = event.get("channel")
            text = event.get("text", "")
            user = event.get("user")
            ts = event.get("ts")
            
            # Handle direct messages (channel_type = 'im')
            if channel_type == "im":
                logger.info(f"Processing direct message from user {user}")
                
                # Get user info
                user_info = await self.slack_client.get_user_info(user)
                user_name = user_info.get("user", {}).get("name", "User")
                
                # Clean the text (remove any @mentions)
                import re
                clean_text = re.sub(r'<@[^>]+>\s*', '', text).strip()
                
                logger.info(f"Processing DM from {user_name}: {clean_text}")
                
                if not clean_text:
                    # Show help message if no text provided
                    help_text = self._get_ai_help_message()
                    await self.slack_client.send_message(
                        channel=channel,
                        text=help_text
                    )
                    return {
                        "ok": True,
                        "message": "AI help message sent for empty DM",
                        "received": event,
                        "error": None
                    }
                
                # Send initial "thinking" message
                thinking_msg = await self.slack_client.send_message(
                    channel=channel,
                    text=f"🤖 *Processing your request:* _{clean_text}_\n⏳ Thinking..."
                )
                
                # Build context for AI router
                context = {
                    "user_id": user,
                    "user_name": user_name,
                    "channel_id": channel,
                    "platform": "slack",
                    "interaction_type": "direct_message"
                }
                
                # Get AI response
                ai_result = await self.ai_router.process_request(
                    user_input=clean_text,
                    context=context
                )
                
                # Format response
                response_text = self._format_ai_response(ai_result, user_name)
                
                # Update the thinking message with the actual response
                if thinking_msg.get("ts"):
                    await self.slack_client.update_message(
                        channel=channel,
                        ts=thinking_msg["ts"],
                        text=response_text
                    )
                else:
                    # Fallback: send new message
                    await self.slack_client.send_message(
                        channel=channel,
                        text=response_text
                    )
                
                # Add completion reaction
                await self.slack_client.react_to_message(
                    channel=channel,
                    timestamp=thinking_msg.get("ts") or ts,
                    reaction="white_check_mark"
                )
                
                return {
                    "ok": True,
                    "message": "Direct message processed successfully",
                    "received": event,
                    "error": None
                }
            
            # For channel messages, only respond if bot is explicitly mentioned
            elif "<@" in text and "app_mentions:read" in ["app_mentions:read"]:  # Bot mentioned in channel
                # This will be handled by _handle_mention instead
                return {
                    "ok": True,
                    "message": "Channel mention will be handled by mention handler",
                    "received": event,
                    "error": None
                }
            
            # For other messages (channels without mentions), just acknowledge
            return {
                "ok": True,
                "message": "Message received but not processed (DM or mention required)",
                "received": event,
                "error": None
            }
            
        except Exception as e:
            logger.exception("Error handling message")
            
            # Send error message to user if we can identify the channel
            try:
                channel = event.get("channel")
                if channel:
                    error_text = f"❌ Sorry, I encountered an error processing your message:\n```{str(e)}```"
                    await self.slack_client.send_message(
                        channel=channel,
                        text=error_text
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
            
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": event
            }
    
    def _get_ai_help_message(self) -> str:
        """Get help message for AI functionality."""
        return """🤖 **AI Assistant Help**

I can help you with various tasks using advanced AI! Just mention me with your question:

**💬 General Questions:**
• `@bot What is machine learning?`
• `@bot Explain REST APIs to me`

**🗄️ Database Queries:**
• `@bot Show me failed tests from yesterday`
• `@bot Count how many tests passed this week`

**💻 Code Generation:**
• `@bot Write a Python function to calculate fibonacci numbers`
• `@bot Create a JavaScript function that validates emails`

**🎯 Smart Routing:**
I automatically detect what type of request you're making and route it to the best AI service:
• **NL2SQL** - For database questions
• **Code Generation** - For programming tasks  
• **General Chat** - For conversations and explanations

Just mention me with `@bot` followed by your question or request!"""
    
    def _format_ai_response(self, ai_result: Dict[str, Any], user_name: str) -> str:
        """Format the AI response for Slack."""
        try:
            if not ai_result.get("success"):
                return f"❌ Sorry {user_name}, I couldn't process your request: {ai_result.get('error', 'Unknown error')}"
            
            # Get routing information
            routing = ai_result.get("routing", {})
            service = routing.get("service", "unknown")
            confidence = routing.get("confidence", 0)
            reasoning = routing.get("reasoning", "No reasoning provided")
            
            # Build response based on service type
            response_parts = [f"🤖 **AI Response for {user_name}**"]
            
            # Add service routing info
            service_emoji = {
                "nl2sql": "🗄️",
                "code_generation": "💻", 
                "general_chat": "💬"
            }
            emoji = service_emoji.get(service, "🤖")
            response_parts.append(f"{emoji} *Routed to: {service.replace('_', ' ').title()}* (confidence: {confidence:.0%})")
            
            # Add main content based on service type
            if service == "nl2sql":
                # Handle NL2SQL responses with table results
                if "formatted_table" in ai_result:
                    # Show the formatted table results
                    row_count = ai_result.get("row_count", 0)
                    response_parts.append(f"\n📊 **Query Results** ({row_count} rows):")
                    
                    # Use compact table format for better mobile experience
                    db_service = DatabaseService()
                    
                    # Create a compact, mobile-friendly display
                    if ai_result.get("results"):
                        compact_table = db_service.format_results_as_compact_table(
                            ai_result["results"], 
                            max_rows=10
                        )
                        response_parts.append(compact_table)
                    else:
                        response_parts.append(ai_result["formatted_table"])
                    
                    # Show the SQL query in a collapsed section
                    if "sql_query" in ai_result:
                        response_parts.append(f"\n🔍 **Generated SQL:**")
                        response_parts.append(f"```sql\n{ai_result['sql_query']}\n```")
                    
                    # Add explanation
                    if "explanation" in ai_result:
                        response_parts.append(f"📝 **Explanation:** {ai_result['explanation']}")
                        
                elif "sql_query" in ai_result:
                    # Fallback to just showing SQL if no table results
                    response_parts.append(f"\n📊 **Generated SQL:**")
                    response_parts.append(f"```sql\n{ai_result['sql_query']}\n```")
                    if "explanation" in ai_result:
                        response_parts.append(f"📝 **Explanation:** {ai_result['explanation']}")
                    
            elif service == "code_generation" and "code" in ai_result:
                language = ai_result.get("language", "code")
                response_parts.append(f"\n💻 **Generated {language.title()}:**")
                response_parts.append(f"```{language}\n{ai_result['code']}\n```")
                if "explanation" in ai_result:
                    response_parts.append(f"📝 **Explanation:** {ai_result['explanation']}")
                if "usage_example" in ai_result:
                    response_parts.append(f"🎯 **Usage:** {ai_result['usage_example']}")
                    
            elif service == "general_chat" and "response" in ai_result:
                response_parts.append(f"\n💬 {ai_result['response']}")
                
            else:
                # Fallback for unknown response format
                response_parts.append(f"\n{ai_result}")
            
            # Add footer
            response_parts.append(f"\n_Reasoning: {reasoning}_")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting AI response: {e}")
            return f"✅ AI processing completed for {user_name}, but there was an issue formatting the response." 