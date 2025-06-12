"""Tests for Slack command handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.commands.hello_command import HelloCommandHandler
from src.bot.commands.connect_slack_command import ConnectSlackCommandHandler
from src.bot.client import SlackClient


@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    client = MagicMock(spec=SlackClient)
    client.send_message = AsyncMock()
    client.send_ephemeral_message = AsyncMock()
    client.get_user_info = AsyncMock()
    client.react_to_message = AsyncMock()
    return client


@pytest.fixture
def sample_command_data():
    """Sample command data from Slack."""
    return {
        "command": "/hello",
        "text": "test message",
        "user_id": "U123456789",
        "user_name": "testuser",
        "channel_id": "C123456789",
        "team_id": "T123456789",
        "response_url": "https://hooks.slack.com/commands/1234/5678"
    }


class TestHelloCommandHandler:
    """Test the hello command handler."""
    
    @pytest.mark.asyncio
    async def test_hello_command_basic(self, mock_slack_client, sample_command_data):
        """Test basic hello command functionality."""
        # Setup
        handler = HelloCommandHandler(mock_slack_client)
        mock_slack_client.get_user_info.return_value = {
            "user": {"real_name": "Test User"}
        }
        mock_slack_client.send_message.return_value = {"ok": True}
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify
        assert result["ok"] is True
        assert result["message"] == "Greeting sent successfully"
        assert result["error"] is None
        
        # Verify Slack API calls
        mock_slack_client.get_user_info.assert_called_once_with("U123456789")
        mock_slack_client.send_message.assert_called_once()
        
        # Check the message content
        call_args = mock_slack_client.send_message.call_args
        assert call_args[1]["channel"] == "C123456789"
        assert "Test User" in call_args[1]["text"]
    
    @pytest.mark.asyncio
    async def test_hello_command_with_text(self, mock_slack_client, sample_command_data):
        """Test hello command with additional text."""
        # Setup
        sample_command_data["text"] = "How are you?"
        handler = HelloCommandHandler(mock_slack_client)
        mock_slack_client.get_user_info.return_value = {
            "user": {"real_name": "Test User"}
        }
        mock_slack_client.send_message.return_value = {"ok": True}
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify
        assert result["ok"] is True
        call_args = mock_slack_client.send_message.call_args
        assert "How are you?" in call_args[1]["text"]
    
    @pytest.mark.asyncio
    async def test_hello_command_user_info_failure(self, mock_slack_client, sample_command_data):
        """Test hello command when user info fails."""
        # Setup
        handler = HelloCommandHandler(mock_slack_client)
        mock_slack_client.get_user_info.side_effect = Exception("API Error")
        mock_slack_client.send_message.return_value = {"ok": True}
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify - should still work with username fallback
        assert result["ok"] is True
        call_args = mock_slack_client.send_message.call_args
        assert "testuser" in call_args[1]["text"]
    
    @pytest.mark.asyncio
    async def test_hello_command_send_message_failure(self, mock_slack_client, sample_command_data):
        """Test hello command when sending message fails."""
        # Setup
        handler = HelloCommandHandler(mock_slack_client)
        mock_slack_client.get_user_info.return_value = {
            "user": {"real_name": "Test User"}
        }
        mock_slack_client.send_message.side_effect = Exception("Send failed")
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify
        assert result["ok"] is False
        assert "Send failed" in result["error"]


class TestConnectSlackCommandHandler:
    """Test the connect Slack command handler."""
    
    @pytest.mark.asyncio
    async def test_connect_command_basic(self, mock_slack_client, sample_command_data):
        """Test basic connect command functionality."""
        # Setup
        sample_command_data["command"] = "/connect-slack"
        sample_command_data["text"] = ""
        handler = ConnectSlackCommandHandler(mock_slack_client)
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify
        assert result["ok"] is True
        assert "connect your account" in result["message"]
        assert "https://a63d65233152.ngrok.app/auth/connect-slack" in result["message"]
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_connect_command_with_user_context(self, mock_slack_client, sample_command_data):
        """Test connect command includes user context in URL."""
        # Setup
        sample_command_data["command"] = "/connect-slack"
        sample_command_data["text"] = ""
        handler = ConnectSlackCommandHandler(mock_slack_client)
        
        # Execute
        result = await handler.handle(sample_command_data)
        
        # Verify URL contains user context
        assert "slack_user_id=U123456789" in result["message"]
        assert "team_id=T123456789" in result["message"]


class TestSlackClient:
    """Test the Slack client wrapper."""
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending a message."""
        with patch('src.bot.client.AsyncWebClient') as mock_client_class:
            # Setup
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_response = MagicMock()
            mock_response.data = {"ok": True, "ts": "1234567890.123456"}
            mock_client.chat_postMessage.return_value = mock_response
            
            client = SlackClient("<SLACK_TOKEN>")
            
            # Execute
            result = await client.send_message(
                channel="C123456789",
                text="Test message"
            )
            
            # Verify
            assert result["ok"] is True
            mock_client.chat_postMessage.assert_called_once_with(
                channel="C123456789",
                text="Test message"
            )
    
    @pytest.mark.asyncio
    async def test_send_ephemeral_message(self):
        """Test sending an ephemeral message."""
        with patch('src.bot.client.AsyncWebClient') as mock_client_class:
            # Setup
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_response = MagicMock()
            mock_response.data = {"ok": True}
            mock_client.chat_postEphemeral.return_value = mock_response
            
            client = SlackClient("<SLACK_TOKEN>")
            
            # Execute
            result = await client.send_ephemeral_message(
                user_id="U123456789",
                channel="C123456789",
                text="Secret message"
            )
            
            # Verify
            assert result["ok"] is True
            mock_client.chat_postEphemeral.assert_called_once_with(
                channel="C123456789",
                user="U123456789",
                text="Secret message"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_info(self):
        """Test getting user info."""
        with patch('src.bot.client.AsyncWebClient') as mock_client_class:
            # Setup
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_response = MagicMock()
            mock_response.data = {
                "ok": True,
                "user": {
                    "id": "U123456789",
                    "name": "testuser",
                    "real_name": "Test User"
                }
            }
            mock_client.users_info.return_value = mock_response
            
            client = SlackClient("<SLACK_TOKEN>")
            
            # Execute
            result = await client.get_user_info("U123456789")
            
            # Verify
            assert result["ok"] is True
            assert result["user"]["real_name"] == "Test User"
            mock_client.users_info.assert_called_once_with(user="U123456789") 