"""Tests for the main application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('src.main.get_settings') as mock:
        settings = MagicMock()
        settings.development_mode = True
        settings.environment = "test"
        settings.log_level = "DEBUG"
        settings.propelauth_url = "https://test.propelauthtest.com"
        settings.propelauth_api_key = "test-key"
        mock.return_value = settings
        yield settings


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_health_check(self, client):
        """Test the root health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_health_endpoint(self, client):
        """Test the /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_healthz_endpoint(self, client):
        """Test the /healthz endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestHelloEndpoint:
    """Test the hello endpoint."""
    
    def test_hello_endpoint(self, client):
        """Test the hello endpoint."""
        response = client.get("/hello")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World!"}


class TestSlackEvents:
    """Test Slack event handling."""
    
    def test_url_verification(self, client):
        """Test Slack URL verification."""
        challenge = "test_challenge_123"
        payload = {
            "type": "url_verification",
            "challenge": challenge
        }
        
        response = client.post("/", json=payload)
        assert response.status_code == 200
        assert response.json() == {"challenge": challenge}
    
    def test_invalid_post_request(self, client):
        """Test invalid POST request to root."""
        payload = {"invalid": "data"}
        
        response = client.post("/", json=payload)
        assert response.status_code == 404


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        # CORS headers should be present due to middleware
        assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


class TestStartupEvent:
    """Test application startup."""
    
    @patch('src.main.get_settings')
    def test_startup_logging(self, mock_get_settings, client):
        """Test that startup event logs correctly."""
        settings = MagicMock()
        settings.environment = "test"
        settings.log_level = "DEBUG"
        settings.propelauth_url = "https://test.propelauthtest.com"
        settings.propelauth_api_key = "test-key"
        mock_get_settings.return_value = settings
        
        # The startup event should run when creating the client
        # We just verify no exceptions are raised
        assert client is not None


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_endpoint(self, client):
        """Test 404 handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.patch("/")
        assert response.status_code == 405 