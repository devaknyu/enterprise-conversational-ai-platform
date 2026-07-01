"""Pydantic models for conversation session state."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel


class SessionAction(BaseModel):
    """A single recorded action within a conversation session."""

    action: str
    session_id: str
    timestamp: datetime
    metadata: dict[str, Any] = {}


class SessionState(BaseModel):
    """Aggregated state for a Dialogflow conversation session."""

    session_id: str
    actions: list[SessionAction] = []
    created_at: datetime
    last_updated: datetime
