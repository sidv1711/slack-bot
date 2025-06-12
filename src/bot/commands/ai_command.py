"""AI command handler for Slack bot integration."""
from typing import Dict, Any
from loguru import logger

from ..types import SlackCommand, SlackResponse
from .base import BaseCommandHandler
from ...services.ai_router_service import AIRouterService

class AICommandHandler(BaseCommandHandler):
    """Handler for AI-related commands."""
    
    def __init__(self, slack_client, ai_router: AIRouterService = None):
        """Initialize the AI command handler."""
        super().__init__(slack_client)
        self.ai_router = ai_router or AIRouterService()
        
    async def handle(self, command_data: SlackCommand) -> SlackResponse:
        """Handle AI-related slash commands."""
        try:
            text = command_data.get("text", "").strip()
            user_id = command_data.get("user_id")
            user_name = command_data.get("user_name", "User")
            channel_id = command_data.get("channel_id")
            
            if not text:
                # Show help message
                help_text = self._get_help_message()
                await self.slack_client.send_message(
                    channel=channel_id,
                    text=help_text
                )
                return {
                    "ok": True,
                    "message": "AI help message sent",
                    "received": command_data,
                    "error": None
                }
            
            # Process the AI request
            logger.info(f"Processing AI request from {user_name}: {text}")
            
            # Build context for AI router
            context = {
                "user_id": user_id,
                "user_name": user_name,
                "channel_id": channel_id,
                "platform": "slack"
            }
            
            # Send initial "thinking" message
            thinking_msg = await self.slack_client.send_message(
                channel=channel_id,
                text=f"🤖 Processing your request: _{text}_\n⏳ Thinking..."
            )
            
            # Get AI response
            ai_result = await self.ai_router.process_request(
                user_input=text,
                context=context
            )
            
            # Format and send response
            response_text = self._format_ai_response(ai_result, user_name)
            
            # Update the thinking message with the actual response
            if thinking_msg.get("ts"):
                await self.slack_client.update_message(
                    channel=channel_id,
                    ts=thinking_msg["ts"],
                    text=response_text
                )
            else:
                # Fallback: send new message
                await self.slack_client.send_message(
                    channel=channel_id,
                    text=response_text
                )
            
            # Add reaction to indicate completion
            await self.slack_client.react_to_message(
                channel=channel_id,
                timestamp=thinking_msg.get("ts") or "",
                reaction="white_check_mark"
            )
            
            return {
                "ok": True,
                "message": "AI request processed successfully",
                "received": command_data,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error processing AI command: {str(e)}")
            
            # Send error message to user
            error_text = f"❌ Sorry {user_name}, I encountered an error processing your request:\n```{str(e)}```"
            
            try:
                await self.slack_client.send_message(
                    channel=command_data.get("channel_id"),
                    text=error_text
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
            
            return {
                "ok": False,
                "error": str(e),
                "message": None,
                "received": command_data
            }
    
    def _get_help_message(self) -> str:
        """Get help message for the AI command."""
        return """🤖 **AI Assistant Help**

I can help you with various tasks using advanced AI:

**💬 General Questions:**
• `/ai What is machine learning?`
• `/ai Explain REST APIs to me`

**🗄️ Database Queries:**
• `/ai Show me failed tests from yesterday`
• `/ai Count how many tests passed this week`

**💻 Code Generation:**
• `/ai Write a Python function to calculate fibonacci numbers`
• `/ai Create a JavaScript function that validates emails`

**🎯 Smart Routing:**
I automatically detect what type of request you're making and route it to the best AI service:
• **NL2SQL** - For database questions
• **Code Generation** - For programming tasks  
• **General Chat** - For conversations and explanations

Just type `/ai` followed by your question or request!"""
    
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
            if service == "nl2sql" and "sql_query" in ai_result:
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