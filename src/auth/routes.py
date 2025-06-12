"""OAuth routes for Slack authentication."""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import Installation
from ..config.settings import get_settings
from slack_sdk.web.async_client import AsyncWebClient
from .store import StateStore, MemoryInstallationStore
from .supabase_store import SupabaseInstallationStore, SupabaseUserMappingStore

router = APIRouter()
settings = get_settings()

# Log settings at module level
logger.info("OAuth settings loaded:")
logger.info(f"Client ID: {settings.slack_client_id}")
logger.info(f"Redirect URI: {settings.slack_oauth_redirect_uri}")
logger.info(f"Development Mode: {settings.development_mode}")

# Initialize our stores
state_store = StateStore()
installation_store = SupabaseInstallationStore(settings) if not settings.development_mode else MemoryInstallationStore()

# Initialize the authorize URL generator
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=settings.slack_client_id,
    scopes=[
        "chat:write",           # Base permission for posting messages
        "chat:write.public",    # Post in any public channel
        "chat:write.customize", # Customize message formatting
        "reactions:write", 
        "users:read",
        "commands",
        "app_mentions:read",
        "channels:join",
        "im:read",
        "im:write",
        "im:history"
        "incoming-webhook"
    ],
    user_scopes=[],  # Add user scopes if needed
    redirect_uri=settings.slack_oauth_redirect_uri
)

@router.get("/slack/install")
async def install_slack_app(request: Request) -> RedirectResponse:
    """Start the Slack OAuth flow by redirecting to Slack's authorization page."""
    try:
        logger.info("Starting Slack OAuth installation flow")
        logger.info(f"Client ID being used: {settings.slack_client_id}")
        logger.info(f"Redirect URI being used: {settings.slack_oauth_redirect_uri}")
        
        # Generate and store state parameter for CSRF protection
        state = state_store.issue()
        logger.info(f"Generated state parameter: {state}")
        
        # Generate the authorization URL
        authorize_url = authorize_url_generator.generate(state)
        logger.info(f"Generated authorization URL: {authorize_url}")
        
        # Log the full URL for debugging
        logger.info("Full authorization URL components:")
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(authorize_url)
        query_params = parse_qs(parsed.query)
        for key, value in query_params.items():
            if key in ['client_id', 'scope', 'state', 'redirect_uri']:
                logger.info(f"{key}: {value[0]}")
        
        # Redirect to Slack's authorization page
        logger.info("Redirecting to Slack's authorization page")
        return RedirectResponse(url=authorize_url)
        
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@router.get("/slack/callback")
async def handle_oauth_callback(
    code: str,
    state: str,
    request: Request
) -> Dict[str, Any]:
    """Handle the OAuth callback from Slack."""
    try:
        logger.info("Received OAuth callback")
        logger.info(f"Code present: {bool(code)}")
        logger.info(f"State present: {bool(state)}")
        
        # Verify state parameter
        if not state_store.consume(state):
            logger.error("Invalid or expired state parameter")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        logger.info("State parameter verified")
        
        # Exchange the temporary code for tokens
        client = AsyncWebClient()  # Token not needed for this call
        logger.info("Exchanging code for tokens")
        oauth_response = await client.oauth_v2_access(
            client_id=settings.slack_client_id,
            client_secret=settings.slack_client_secret,
            code=code,
            redirect_uri=settings.slack_oauth_redirect_uri
        )
        
        logger.info("Received OAuth response")
        logger.info(f"OAuth response ok: {oauth_response.get('ok')}")
        
        if not oauth_response.get("ok"):
            error = oauth_response.get("error", "Unknown error")
            logger.error(f"OAuth exchange failed: {error}")
            raise ValueError(f"OAuth exchange failed: {error}")
            
        # Store the installation
        installation = Installation(
            app_id=oauth_response["app_id"],
            enterprise_id=oauth_response.get("enterprise_id"),
            team_id=oauth_response["team"]["id"],
            bot_token=oauth_response["access_token"],
            bot_id=oauth_response["bot_user_id"],
            bot_scopes=oauth_response["scope"].split(","),
            user_id=oauth_response["authed_user"]["id"]
        )
        
        logger.info(f"Created installation for team {installation.team_id}")
        
        # Store the installation
        await installation_store.save(installation)
        logger.info("Installation saved")
        
        # Redirect to a success page or back to Slack
        redirect_url = f"https://slack.com/app_redirect?app={installation.app_id}"
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed") 