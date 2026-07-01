"""Unit tests for SessionService. Implemented in Phase 3b."""

import pytest

from app.services.business.session_service import SessionService

_SESSION_A = "projects/test/locations/us-central1/agents/ag/sessions/sess-001"
_SESSION_B = "projects/test/locations/us-central1/agents/ag/sessions/sess-002"


class TestSessionService:
    """Unit tests for SessionService.record_action() and get_session()."""

    async def test_record_action_creates_new_session(self, test_logger):
        """First record_action call on an unknown session_id creates a SessionState."""
        svc = SessionService(logger=test_logger)

        await svc.record_action(session_id=_SESSION_A, action="password_reset")

        state = await svc.get_session(_SESSION_A)
        assert state is not None
        assert state.session_id == _SESSION_A
        assert len(state.actions) == 1
        assert state.actions[0].action == "password_reset"

    async def test_record_action_appends_to_existing_session(self, test_logger):
        """Subsequent record_action calls append to the same SessionState."""
        svc = SessionService(logger=test_logger)

        await svc.record_action(session_id=_SESSION_A, action="user_verified")
        await svc.record_action(session_id=_SESSION_A, action="password_reset")

        state = await svc.get_session(_SESSION_A)
        assert state is not None
        assert len(state.actions) == 2
        assert state.actions[0].action == "user_verified"
        assert state.actions[1].action == "password_reset"

    async def test_record_action_stores_metadata(self, test_logger):
        """Metadata dict is preserved verbatim in the recorded SessionAction."""
        svc = SessionService(logger=test_logger)
        meta = {"user_id": "john.doe@acme.com", "ticket": "INC0001234"}

        await svc.record_action(session_id=_SESSION_A, action="ticket_created", metadata=meta)

        state = await svc.get_session(_SESSION_A)
        assert state is not None
        assert state.actions[0].metadata == meta

    async def test_get_session_returns_none_for_unknown_session_id(self, test_logger):
        """get_session() returns None when no actions have been recorded for the ID."""
        svc = SessionService(logger=test_logger)

        result = await svc.get_session(_SESSION_B)

        assert result is None

    async def test_get_session_isolates_separate_sessions(self, test_logger):
        """Actions recorded for session A do not appear in session B."""
        svc = SessionService(logger=test_logger)

        await svc.record_action(session_id=_SESSION_A, action="password_reset")
        await svc.record_action(session_id=_SESSION_B, action="ticket_created")

        state_a = await svc.get_session(_SESSION_A)
        state_b = await svc.get_session(_SESSION_B)
        assert state_a is not None and len(state_a.actions) == 1
        assert state_b is not None and len(state_b.actions) == 1
        assert state_a.actions[0].action == "password_reset"
        assert state_b.actions[0].action == "ticket_created"
