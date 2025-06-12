"""Common test fixtures and configuration."""
import os
import pytest
from src.config.settings import Settings
from src.bot.services import SlackService
from src.bot.client import SlackClient
from unittest.mock import AsyncMock

# Set test environment variables before importing app
os.environ.update({
    "DEVELOPMENT_MODE": "true",
    "SLACK_BOT_TOKEN": "<SLACK_TOKEN>",
    "SLACK_SIGNING_SECRET": "test-signing-secret",
    "SLACK_CLIENT_ID": "test-client-id",
    "SLACK_CLIENT_SECRET": "test-client-secret",
    "SLACK_OAUTH_REDIRECT_URI": "http://localhost:8000/auth/slack/callback",
    "PROPELAUTH_API_KEY": "test-propel-key",
    "PROPELAUTH_URL": "https://test.propelauth.com",
    "PROPELAUTH_REDIRECT_URI": "http://localhost:8000/auth/propel/callback",
    "PROPELAUTH_CLIENT_ID": "test-propel-client-id",
    "PROPELAUTH_CLIENT_SECRET": "test-propel-client-secret",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "test-supabase-key",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
    "OPENAI_API_KEY": "test-openai-key",  # Optional for development
    "AI_SERVICE_URL": "http://localhost:8001",
    "AI_SERVICE_ENABLED": "false",  # Disable AI service for tests
})

from src.main import app

@pytest.fixture
def settings() -> Settings:
    """Provide a test settings instance."""
    return Settings(
        development_mode=True,
        log_level="DEBUG",
        slack_bot_token="<SLACK_TOKEN>",
        slack_signing_secret="test-secret",
        slack_app_token="xapp-test-token",
        slack_client_id="test-client-id",
        slack_client_secret="test-client-secret",
        slack_oauth_redirect_uri="https://test.com/auth/slack/callback",
        propelauth_api_key="test-api-key",
        propelauth_url="https://test.propelauthtest.com",
        propelauth_redirect_uri="https://test.com/auth/callback/propelauth",
        propelauth_client_id="test-propel-client-id",
        propelauth_client_secret="test-propel-client-secret",
        supabase_url="https://test.supabase.co",
        supabase_key="test-supabase-key",
        supabase_service_role_key="test-service-role-key"
    )

@pytest.fixture
def mock_slack_client() -> SlackClient:
    """Create a mock Slack client."""
    client = AsyncMock(spec=SlackClient)
    client.send_message = AsyncMock(return_value={"ok": True})
    client.react_to_message = AsyncMock(return_value={"ok": True})
    client.get_user_info = AsyncMock(return_value={"ok": True, "user": {"name": "testuser"}})
    return client

@pytest.fixture
def slack_service(settings: Settings) -> SlackService:
    """Provide a test SlackService instance."""
    return SlackService(development_mode=True)

@pytest.fixture
def mock_event_data() -> dict:
    """Provide mock Slack event data."""
    return {
        "type": "event_callback",
        "team_id": "T123ABC",
        "event": {
            "type": "app_mention",
            "user": "U061F7AUR",
            "text": "Hey bot!",
            "ts": "1515449522.000016",
            "channel": "C123456",
        },
        "event_id": "Ev123ABC",
        "event_time": 1515449522
    }

@pytest.fixture
def mock_command_data() -> dict:
    """Provide mock Slack command data."""
    return {
        "command": "/hello",
        "text": "",
        "user_id": "U061F7AUR",
        "user_name": "testuser",
        "channel_id": "C123456",
        "team_id": "T123ABC"
    } 

@pytest.fixture
def test_app():
    """Provide the FastAPI app for testing."""
    return app

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock = AsyncMock()
    mock.process_request.return_value = {
        "success": True,
        "response": "Test AI response",
        "routing": {"service": "test", "confidence": 1.0}
    }
    return mock 