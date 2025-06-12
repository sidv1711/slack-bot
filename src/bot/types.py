"""Type definitions for Slack events and responses."""
from typing import Literal, Optional, Dict, Any
from typing_extensions import TypedDict

class SlackUser(TypedDict):
    """Slack user information."""
    id: str
    name: Optional[str]
    team_id: Optional[str]

class SlackEvent(TypedDict):
    """Base Slack event structure."""
    type: str
    user: str
    ts: str
    channel: Optional[str]
    text: Optional[str]

class SlackEventCallback(TypedDict):
    """Slack event callback structure."""
    token: str
    team_id: str
    event: SlackEvent
    type: Literal["event_callback"]
    event_id: str
    event_time: int

class SlackCommand(TypedDict):
    """Slack command structure."""
    command: str
    text: str
    user_id: str
    user_name: str
    channel_id: str
    team_id: str

class SlackResponse(TypedDict):
    """Standard response structure."""
    ok: bool
    message: Optional[str]
    error: Optional[str]
    received: Optional[Dict[str, Any]] 