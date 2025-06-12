"""Models for user mapping between Slack and PropelAuth."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserMapping(BaseModel):
    """Mapping between Slack and PropelAuth user IDs."""
    slack_user_id: str
    propelauth_user_id: str
    slack_team_id: str
    slack_email: Optional[str] = None
    propelauth_email: str
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow() 