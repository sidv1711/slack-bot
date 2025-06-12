"""Tests for the FastAPI request handlers."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.bot.handlers import router
from src.bot.services import SlackService
from src.config.settings import Settings, get_settings
from src.bot.dependencies import get_slack_client
from typing import Generator

@pytest.fixture
def app(settings: Settings, mock_slack_client) -> FastAPI:
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(router, prefix="/slack")
    
    def get_test_settings():
        return settings
        
    def get_test_slack_client():
        return mock_slack_client
    
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_slack_client] = get_test_slack_client
    return app

@pytest.fixture
def client(app: FastAPI) -> Generator:
    """Create a test client."""
    with TestClient(app) as client:
        yield client

def test_handle_slack_event_success(client: TestClient, mock_event_data: dict):
    """Test successful event handling."""
    response = client.post("/slack/events", json=mock_event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "Event processed in development mode" in data["message"]
    assert data["received"] == mock_event_data

def test_handle_slack_event_invalid_data(client: TestClient):
    """Test handling invalid event data."""
    response = client.post("/slack/events", json={})
    assert response.status_code == 200  # We still return 200 but with error in response
    data = response.json()
    assert data["ok"] is False
    assert data["error"] is not None

def test_handle_slack_command_success(client: TestClient, mock_command_data: dict):
    """Test successful command handling."""
    # Convert dict to form data
    response = client.post(
        "/slack/commands/hello",
        data={
            "command": "/hello",
            "text": mock_command_data.get("text", ""),
            "user_id": mock_command_data.get("user_id", "U123ABC"),
            "user_name": mock_command_data.get("user_name", "testuser"),
            "channel_id": mock_command_data.get("channel_id", "C123456"),
            "team_id": mock_command_data.get("team_id", "T123ABC")
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "Command processed in development mode" in data["message"]

def test_handle_slack_command_invalid_data(client: TestClient):
    """Test handling invalid command data."""
    response = client.post("/slack/commands/hello", data={})
    assert response.status_code == 422  # FastAPI validation error for missing required fields 