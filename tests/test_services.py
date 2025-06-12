"""Tests for the SlackService class."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot.services import SlackService
from src.bot.client import SlackClient
from src.bot.types import SlackResponse

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    client = AsyncMock(spec=SlackClient)
    client.send_message = AsyncMock(return_value={"ok": True})
    client.react_to_message = AsyncMock(return_value={"ok": True})
    client.get_user_info = AsyncMock(return_value={"ok": True, "user": {"name": "testuser"}})
    return client

async def test_handle_event_development_mode(slack_service: SlackService, mock_event_data: dict):
    """Test handling events in development mode."""
    response = await slack_service.handle_event(mock_event_data)
    assert isinstance(response, dict)
    assert response["ok"] is True
    assert "Event processed in development mode" in response["message"]
    assert response["received"] == mock_event_data
    assert response["error"] is None

async def test_handle_event_production_mode(mock_slack_client):
    """Test handling events in production mode."""
    service = SlackService(development_mode=False, slack_client=mock_slack_client)
    mock_event = {
        "event": {
            "type": "app_mention",
            "user": "U123",
            "text": "hello",
            "channel": "C123",
            "ts": "1234567890.123456"
        },
        "event_id": "Ev123",
        "team_id": "T123",
        "api_app_id": "A123"
    }
    
    response = await service.handle_event(mock_event)
    assert isinstance(response, dict)
    assert response["ok"] is True
    mock_slack_client.send_message.assert_called_once_with(
        channel="C123",
        text="Hi @testuser! You said: hello"
    )

async def test_handle_event_error():
    """Test handling events with errors."""
    service = SlackService()
    # Pass None to trigger an error
    response = await service.handle_event(None)  # type: ignore
    assert isinstance(response, dict)
    assert response["ok"] is False
    assert response["error"] is not None
    assert response["received"] is None

async def test_handle_command_development_mode(slack_service: SlackService, mock_command_data: dict):
    """Test handling commands in development mode."""
    response = await slack_service.handle_command(mock_command_data)
    assert isinstance(response, dict)
    assert response["ok"] is True
    assert "Command processed in development mode" in response["message"]
    assert response["received"] == mock_command_data
    assert response["error"] is None

async def test_handle_command_production_mode(mock_slack_client):
    """Test handling commands in production mode."""
    service = SlackService(development_mode=False, slack_client=mock_slack_client)
    mock_command = {
        "command": "/hello",
        "text": "hello",
        "user_id": "U123",
        "user_name": "testuser",
        "channel_id": "C123",
        "team_id": "T123"
    }
    
    response = await service.handle_command(mock_command)
    assert isinstance(response, dict)
    assert response["ok"] is True
    mock_slack_client.send_message.assert_called_once()

async def test_handle_command_error():
    """Test handling commands with errors."""
    service = SlackService()
    # Pass None to trigger an error
    response = await service.handle_command(None)  # type: ignore
    assert isinstance(response, dict)
    assert response["ok"] is False
    assert response["error"] is not None
    assert response["received"] is None 