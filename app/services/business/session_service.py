"""Session state management service. Implemented in Phase 3b."""

from typing import Any
import structlog

from app.services.business.base import BaseService
from app.models.session import SessionAction, SessionState


class SessionService(BaseService):
    """Manages per-conversation session state and action history.

    Stores session actions in memory (Phase 3b). Production replacement:
    Redis via Cloud Memorystore for distributed session state across
    multiple Cloud Run instances.

    Used by all business services to record audit-trail events.
    """

    def __init__(self, logger: structlog.BoundLogger) -> None:
        super().__init__(logger)

    async def record_action(
        self,
        session_id: str,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an action taken during this conversation session.

        Args:
            session_id: Dialogflow session ID (unique per conversation).
            action: Action name (e.g. "password_reset", "ticket_created").
            metadata: Additional context to store with the action (user IDs,
                ticket numbers, etc.).
        """
        ...

    async def get_session(self, session_id: str) -> SessionState | None:
        """Retrieve the current state of a session.

        Args:
            session_id: Dialogflow session ID to look up.

        Returns:
            SessionState if the session exists, None if not found.
        """
        ...
