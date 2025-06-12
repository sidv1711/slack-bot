"""PropelAuth OAuth routes."""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from loguru import logger
import json
import base64
import httpx
from datetime import datetime
from urllib.parse import quote_plus, urlencode
from .propel import auth
from ..config.settings import get_settings
from .mapping_service import UserMappingService
from .dependencies import get_user_mapping_service
from typing import Optional

router = APIRouter()
settings = get_settings()

@router.get("/login")
async def login():
    """Redirect to PropelAuth hosted login page."""
    auth_url = f"{settings.propelauth_url}/login"
    logger.info(f"Redirecting to PropelAuth login: {auth_url}")
    return RedirectResponse(url=auth_url)

@router.get("/connect-slack")
async def connect_slack(slack_user_id: str, team_id: str):
    """Initiate PropelAuth authentication flow with Slack context."""
    try:
        logger.info("=== Starting Slack Connection Flow ===")
        logger.info(f"Slack User ID: {slack_user_id}")
        logger.info(f"Team ID: {team_id}")
        
        # Create a state parameter with Slack context
        state = {
            "slack_user_id": slack_user_id,
            "team_id": team_id,
            "timestamp": datetime.utcnow().isoformat()  # Add timestamp for verification
        }
        
        # Encode state as base64 to make it URL-safe
        state_encoded = base64.b64encode(json.dumps(state).encode()).decode()
        logger.info(f"Generated state: {state}")
        logger.info(f"Encoded state: {state_encoded}")
        
        # Build the query parameters
        query_params = {
            "redirect_uri": settings.propelauth_redirect_uri,
            "client_id": settings.propelauth_client_id,
            "response_type": "code",
            "state": state_encoded
        }
        
        # Build the auth URL with state parameter and redirect URI
        auth_url = f"{settings.propelauth_url}/propelauth/oauth/authorize?{urlencode(query_params)}"
        logger.info(f"Redirecting to PropelAuth: {auth_url}")
        
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Error in connect_slack: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback/propelauth")
async def auth_callback(
    request: Request,
    mapping_service: UserMappingService = Depends(get_user_mapping_service)
):
    """Handle the OAuth callback from PropelAuth."""
    try:
        logger.info("=== PropelAuth Callback Started ===")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Query parameters: {dict(request.query_params)}")
        
        # Get query parameters manually
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")
        
        logger.info(f"Extracted parameters - code: {bool(code)}, state: {bool(state)}, error: {error}")
        
        # Check for error response
        if error:
            logger.error(f"PropelAuth returned error: {error} - {error_description}")
            raise HTTPException(status_code=400, detail=f"Authentication failed: {error}")
        
        # Validate required parameters
        if not code or not state:
            logger.error("Missing required parameters")
            logger.error(f"Code present: {bool(code)}")
            logger.error(f"State present: {bool(state)}")
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Decode state parameter
        try:
            state_json = base64.b64decode(state).decode()
            state_data = json.loads(state_json)
            slack_user_id = state_data["slack_user_id"]
            team_id = state_data["team_id"]
            logger.info(f"Decoded state: {state_data}")
            logger.info(f"Slack user ID: {slack_user_id}")
            logger.info(f"Team ID: {team_id}")
        except Exception as e:
            logger.error(f"Error decoding state parameter: {e}")
            logger.error(f"Raw state value: {state}")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange the code for tokens using HTTP request
        try:
            logger.info("Exchanging code for tokens...")
            
            # Prepare the token exchange request
            token_url = f"{settings.propelauth_url}/propelauth/oauth/token"
            
            # Create basic auth header
            auth_string = f"{settings.propelauth_client_id}:{settings.propelauth_client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "client_id": settings.propelauth_client_id,
                "code": code,
                "redirect_uri": settings.propelauth_redirect_uri,
                "grant_type": "authorization_code"
            }
            
            logger.info(f"Making token request to: {token_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, headers=headers, data=data)
                
            logger.info(f"Token response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
                
            tokens = response.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                logger.error(f"No access token in response: {tokens}")
                raise HTTPException(status_code=400, detail="No access token received")
                
            logger.info("Successfully exchanged code for tokens")
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Get user info using the access token
        try:
            logger.info("Getting user info...")
            
            userinfo_url = f"{settings.propelauth_url}/propelauth/oauth/userinfo"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                
            if response.status_code != 200:
                logger.error(f"User info request failed with status {response.status_code}: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user info")
                
            user_data = response.json()
            logger.info(f"Got user info for user: {user_data.get('user_id')} ({user_data.get('email')})")
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Create or update user mapping
        try:
            logger.info("Creating/updating user mapping...")
            
            # Create a simple user object from the response
            class SimpleUser:
                def __init__(self, data):
                    self.user_id = data.get('user_id') or data.get('sub')
                    self.email = data.get('email')
                    self.first_name = data.get('first_name')
                    self.last_name = data.get('last_name')
            
            user = SimpleUser(user_data)
            
            mapping = await mapping_service.get_or_create_mapping(
                slack_user_id=slack_user_id,
                team_id=team_id,
                propelauth_user=user
            )
            logger.info(f"Created/updated user mapping: {mapping}")
        except Exception as e:
            logger.error(f"Error creating/updating user mapping: {e}")
            raise HTTPException(status_code=400, detail="Failed to create user mapping")
        
        # Redirect to Slack
        logger.info("Redirecting to Slack...")
        redirect_url = f"https://slack.com/app_redirect?app=A08U0GPMG82"
        logger.info(f"Redirect URL: {redirect_url}")
        
        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Error in auth callback: {e}")
        logger.error("=== PropelAuth Callback Failed ===")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to complete authentication: {str(e)}"
        ) 