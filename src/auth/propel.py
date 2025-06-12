"""PropelAuth client and middleware configuration."""
from typing import Optional
from fastapi import Depends, HTTPException, Request
from propelauth_fastapi import init_auth, User
import httpx
import jwt
from loguru import logger
from ..config.settings import get_settings

settings = get_settings()

# Log settings for debugging
logger.debug(f"Development mode: {settings.development_mode}")
logger.debug(f"Environment: {settings.environment}")
logger.debug(f"PropelAuth URL (raw): {settings.propelauth_url!r}")
logger.debug(f"PropelAuth redirect URI: {settings.propelauth_redirect_uri}")

# Initialize PropelAuth client
if settings.development_mode:
    logger.warning("Running in development mode - PropelAuth authentication will be mocked")
    # Create a mock auth object that always succeeds
    class MockAuth:
        async def require_user(self, request: Request) -> User:
            """Mock user authentication for development."""
            try:
                # Check for Authorization header in development mode
                auth_header = request.headers.get("Authorization", "")
                logger.debug(f"Received Authorization header: {auth_header}")
                
                if not auth_header:
                    logger.debug("No Authorization header found")
                    raise HTTPException(
                        status_code=401,
                        detail="Missing Authorization header",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                # In development mode, accept any authorization header
                logger.info("Development mode: Using mock user data")
                return User(
                    user_id="dev-user-123",
                    org_id_to_org_member_info={
                        "test-org-123": {
                            "org_id": "test-org-123",
                            "org_name": "Test Organization",
                            "user_role": "Admin"
                        }
                    },
                    email="dev@example.com",
                    username="dev_user",
                    first_name="Dev",
                    last_name="User"
                )
            except Exception as e:
                logger.error(f"Error in mock auth: {str(e)}")
                raise
                
        async def exchange_code_for_tokens(self, code: str):
            """Mock token exchange for development."""
            logger.info("Development mode: Mocking token exchange")
            return type("Tokens", (), {"access_token": "mock_access_token"})()
            
        async def get_user_by_access_token(self, access_token: str) -> User:
            """Mock user retrieval for development."""
            logger.info("Development mode: Mocking user retrieval")
            return User(
                user_id="dev-user-123",
                org_id_to_org_member_info={
                    "test-org-123": {
                        "org_id": "test-org-123",
                        "org_name": "Test Organization",
                        "user_role": "Admin"
                    }
                },
                email="dev@example.com",
                username="dev_user",
                first_name="Dev",
                last_name="User"
            )
            
    auth = MockAuth()
else:
    logger.info("Initializing PropelAuth in production mode")
    # For production, we'll implement manual JWT validation
    # since the PropelAuth FastAPI library seems to have issues
    
    class ProductionAuth:
        def __init__(self):
            self.auth_url = settings.propelauth_url.rstrip('/')
            if not self.auth_url.startswith('https://'):
                self.auth_url = f'https://{self.auth_url}'
            
            self.api_key = settings.propelauth_api_key
            self.verifier_key = settings.propelauth_verifier_key
            
            logger.info(f"Production auth initialized with URL: {self.auth_url}")
        
        async def require_user(self, request: Request) -> User:
            """Validate JWT token and return user info."""
            try:
                # Extract Authorization header
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=401,
                        detail="Missing or invalid Authorization header",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                token = auth_header[7:]  # Remove "Bearer " prefix
                
                # Get user info using PropelAuth API
                user_info = await self._get_user_by_token(token)
                
                # Create User object
                return User(
                    user_id=user_info.get("user_id"),
                    org_id_to_org_member_info=user_info.get("org_id_to_org_member_info", {}),
                    email=user_info.get("email"),
                    username=user_info.get("username"),
                    first_name=user_info.get("first_name"),
                    last_name=user_info.get("last_name")
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error validating token: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        async def _get_user_by_token(self, token: str) -> dict:
            """Get user info from PropelAuth API using token."""
            try:
                # Use PropelAuth userinfo endpoint
                userinfo_url = f"{self.auth_url}/propelauth/oauth/userinfo"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(userinfo_url, headers=headers)
                    
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"Successfully validated token for user: {user_data.get('user_id')} ({user_data.get('email')})")
                    return user_data
                elif response.status_code == 401:
                    logger.warning("Token validation failed - invalid or expired token")
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid or expired token",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    logger.error(f"PropelAuth API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=401,
                        detail="Token validation failed",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error calling PropelAuth API: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail="Authentication service error",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        async def exchange_code_for_tokens(self, code: str):
            """Exchange authorization code for tokens."""
            logger.info("Production mode: Exchanging code for tokens")
            # Implementation would go here for OAuth flow
            return type("Tokens", (), {"access_token": "production_access_token"})()
            
        async def get_user_by_access_token(self, access_token: str) -> User:
            """Get user by access token."""
            user_info = await self._get_user_by_token(access_token)
            return User(
                user_id=user_info.get("user_id"),
                org_id_to_org_member_info=user_info.get("org_id_to_org_member_info", {}),
                email=user_info.get("email"),
                username=user_info.get("username"),
                first_name=user_info.get("first_name"),
                last_name=user_info.get("last_name")
            )
    
    auth = ProductionAuth()
    logger.info("Production auth client initialized")

# Create a dependency that will be used to get the current user
async def get_current_user(request: Request) -> Optional[User]:
    """Get the current authenticated user from the request."""
    try:
        # Log request headers for debugging
        logger.debug("=== Authenticating Request ===")
        logger.debug("Request headers:")
        for header, value in request.headers.items():
            logger.debug(f"{header}: {value}")
            
        # This will validate the token and return the user
        user = await auth.require_user(request)
        logger.info(f"Successfully authenticated user: {user.user_id} ({user.email})")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Create a dependency that will require specific org membership
def require_org_member(org_id: str):
    """Create a dependency that requires membership in a specific organization."""
    async def check_org_membership(user: User = Depends(get_current_user)) -> User:
        if not user.org_id_to_org_member_info or org_id not in user.org_id_to_org_member_info:
            raise HTTPException(
                status_code=403,
                detail=f"User is not a member of organization {org_id}"
            )
        return user
    return check_org_membership 