"""Request handlers for Slack events and commands."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from loguru import logger

from .dependencies import get_slack_service
from .services import SlackService
from .types import SlackResponse
from ..utils.logging import log_user_action, log_error_with_context

router = APIRouter()

async def _handle_command(
    command: str,
    text: str,
    user_id: str,
    user_name: str,
    channel_id: str,
    team_id: str,
    slack_service: SlackService
) -> SlackResponse:
    """Common command handler logic."""
    try:
        log_user_action(user_id, f"executed {command} command", f"text: {text}")
        
        command_data = {
            "command": command,
            "text": text,
            "user_id": user_id,
            "user_name": user_name,
            "channel_id": channel_id,
            "team_id": team_id
        }
        
        response = await slack_service.handle_command(command_data)
        logger.debug(f"Command {command} response: {response}")
        return response
        
    except Exception as e:
        log_error_with_context(e, {
            "command": command,
            "user_id": user_id,
            "team_id": team_id,
            "operation": "handle_command"
        })
        return {"ok": False, "error": str(e), "message": None, "received": None}

@router.post("/events")
async def handle_slack_event(request: Request) -> Dict[str, Any]:
    """Handle incoming Slack events."""
    try:
        event_data = await request.json()
        logger.debug(f"Received Slack event: {event_data.get('type', 'unknown')}")
        
        # Handle URL verification challenge first, before any dependency injection
        if event_data.get("type") == "url_verification":
            challenge = event_data.get("challenge")
            logger.info("URL verification challenge received")
            if not challenge:
                raise HTTPException(status_code=400, detail="Challenge value missing")
            return {"challenge": challenge}
            
        # For all other events, get the Slack service
        slack_service = await get_slack_service(request)
        
        if not event_data or not isinstance(event_data, dict):
            logger.error("Invalid event data received")
            return {"ok": False, "error": "Invalid event data"}
            
        return await slack_service.handle_event(event_data)
        
    except Exception as e:
        log_error_with_context(e, {"operation": "handle_slack_event"})
        return {"ok": False, "error": str(e)}

@router.post("/commands/hello")
async def handle_hello_command(
    command: str = Form(...),
    text: str = Form(default=""),
    user_id: str = Form(...),
    user_name: str = Form(...),
    channel_id: str = Form(...),
    team_id: str = Form(...),
    slack_service: SlackService = Depends(get_slack_service)
) -> SlackResponse:
    """Handle the /hello slash command."""
    return await _handle_command(command, text, user_id, user_name, channel_id, team_id, slack_service)

@router.post("/commands/connect-slack")
async def handle_connect_slack_command(
    command: str = Form(...),
    text: str = Form(default=""),
    user_id: str = Form(...),
    user_name: str = Form(...),
    channel_id: str = Form(...),
    team_id: str = Form(...),
    slack_service: SlackService = Depends(get_slack_service)
) -> SlackResponse:
    """Handle the /connect-slack slash command."""
    return await _handle_command(command, text, user_id, user_name, channel_id, team_id, slack_service)

@router.post("/commands/ai")
async def handle_ai_command(
    command: str = Form(...),
    text: str = Form(default=""),
    user_id: str = Form(...),
    user_name: str = Form(...),
    channel_id: str = Form(...),
    team_id: str = Form(...),
    slack_service: SlackService = Depends(get_slack_service)
) -> SlackResponse:
    """Handle the /ai slash command for AI-powered responses."""
    return await _handle_command(command, text, user_id, user_name, channel_id, team_id, slack_service)

@router.post("/commands/test-executions")
async def handle_test_executions_command(
    command: str = Form(...),
    text: str = Form(default=""),
    user_id: str = Form(...),
    user_name: str = Form(...),
    channel_id: str = Form(...),
    team_id: str = Form(...),
    slack_service: SlackService = Depends(get_slack_service)
) -> SlackResponse:
    """Handle the /test-executions slash command for retrieving test execution history."""
    return await _handle_command(command, text, user_id, user_name, channel_id, team_id, slack_service)

@router.post("/interactive")
async def handle_interactive_component(
    request: Request
) -> Dict[str, Any]:
    """Handle interactive component submissions (button clicks, etc.)."""
    try:
        form = await request.form()
        payload_str = form.get("payload")
        
        if not payload_str:
            logger.error("No payload found in interactive request")
            return {"ok": False, "error": "No payload found"}
        
        import json
        payload = json.loads(payload_str)
        
        # Extract action details
        action_id = payload.get("actions", [{}])[0].get("action_id")
        user_id = payload.get("user", {}).get("id")
        user_name = payload.get("user", {}).get("name", "User")
        channel_id = payload.get("channel", {}).get("id")
        team_id = payload.get("team", {}).get("id")
        
        logger.info(f"Interactive action: {action_id} from user {user_id}")
        
        # Handle different action types
        if action_id == "test_executions_help":
            test_id = payload.get("actions", [{}])[0].get("value", "")
            return await _handle_test_executions_help(channel_id, user_id, user_name, test_id, team_id)
        
        logger.warning(f"Unhandled interactive action: {action_id}")
        return {"ok": True, "message": f"Received unhandled action: {action_id}"}
        
    except Exception as e:
        log_error_with_context(e, {"operation": "handle_interactive_component"})
        logger.error(f"Error handling interactive component: {str(e)}")
        return {"ok": False, "error": str(e)}

async def _handle_test_executions_help(
    channel_id: str, 
    user_id: str, 
    user_name: str, 
    test_id: str, 
    team_id: str
) -> Dict[str, Any]:
    """Handle the test executions help button click."""
    try:
        from .client import SlackClient
        from ..config.settings import get_settings
        from ..auth.supabase_store import SupabaseInstallationStore
        
        # Get the team-specific bot token from installation store
        settings = get_settings()
        installation_store = SupabaseInstallationStore(settings)
        installation = await installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id
        )
        
        if not installation or not installation.bot_token:
            logger.error(f"No installation found for team {team_id}")
            return {"ok": False, "error": "No installation found"}
        
        # Create slack client with team-specific token
        slack_client = SlackClient(installation.bot_token)
        
        help_text = f"""🔍 **Troubleshooting Report Access for `{test_id}`**

Hi {user_name}! Having trouble accessing your test reports? Here's how to fix common issues:

**💡 How to Access Reports:**
• **Step 1**: Make sure you're logged in to https://app.example.com with the same email as your Slack account
• **Step 2**: Click the report links above - they'll open directly in your browser
• **Step 3**: If you get "access denied", ensure your Slack and your_company accounts use the same email

**🔍 Troubleshooting 'Link unavailable':**
• **Account Mismatch**: Your Slack email must match your your_company account email
• **Test Permissions**: You may not have access to test `{test_id}` in your_company
• **Login Required**: You must be logged in to app.example.com first

**📧 Need More Help?**
• Run `/connect-slack` to link your accounts
• Contact support if issues persist
• Check that you have permissions for test `{test_id}` in the your_company app"""

        # Send ephemeral message (only visible to the user who clicked)
        await slack_client.send_ephemeral_message(
            user_id=user_id,
            channel=channel_id,
            text=help_text
        )
        
        return {"ok": True, "message": "Help message sent"}
        
    except Exception as e:
        logger.error(f"Error sending help message: {str(e)}")
        return {"ok": False, "error": str(e)}