"""Session state management service. Implemented in Phase 3b."""

from datetime import datetime, timezone
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
        self._store: dict[str, SessionState] = {}

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
        now = datetime.now(timezone.utc)

        if session_id not in self._store:
            self._store[session_id] = SessionState(
                session_id=session_id,
                actions=[],
                created_at=now,
                last_updated=now,
            )

        session = self._store[session_id]
        session.actions.append(
            SessionAction(
                action=action,
                session_id=session_id,
                timestamp=now,
                metadata=metadata or {},
            )
        )
        session.last_updated = now

        self.logger.info(
            "session_action_recorded",
            session_id=session_id,
            action=action,
            action_count=len(session.actions),
        )

    async def get_session(self, session_id: str) -> SessionState | None:
        """Retrieve the current state of a session.

        Args:
            session_id: Dialogflow session ID to look up.

        Returns:
            SessionState if the session exists, None if not found.
        """
        return self._store.get(session_id)
