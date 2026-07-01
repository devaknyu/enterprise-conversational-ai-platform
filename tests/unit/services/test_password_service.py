"""Unit tests for PasswordService. Implemented in Phase 3d.

Tests cover:
- Successful password reset for active users
- UserNotFoundError propagation for unknown users
- IntegrationError → PasswordResetError conversion
- Session action recording on successful reset
- Session action NOT recorded on failure
"""

from datetime import datetime, timezone

import pytest
import structlog

from app.core.exceptions import IntegrationError, PasswordResetError, UserNotFoundError
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult, UserProfile
from app.services.business.password_service import PasswordService
from app.services.business.session_service import SessionService

_SESSION_ID = "test-session-001"
_USER_ID = "john.doe@acme.com"
_FIXED_RESULT = PasswordResetResult(
    success=True,
    user_id=_USER_ID,
    delivery_method="email",
    estimated_delivery_minutes=5,
    ticket_reference="CHG1234567",
    reset_at=datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
)


class _StubADClient(BaseActiveDirectoryClient):
    """Stub AD client with deterministic behaviour for testing."""

    async def get_user_profile(self, user_id: str) -> UserProfile:
        raise NotImplementedError("Not called by PasswordService")

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        if user_id == "unknown@acme.com":
            raise UserNotFoundError(f"User not found: {user_id}")
        if user_id == "error@acme.com":
            raise IntegrationError("AD service unavailable")
        return _FIXED_RESULT


def _make_service() -> tuple[PasswordService, SessionService]:
    logger = structlog.get_logger()
    session_service = SessionService(logger=logger)
    service = PasswordService(
        ad_client=_StubADClient(),
        session_service=session_service,
        logger=logger,
    )
    return service, session_service


class TestPasswordService:
    """Unit tests for PasswordService.initiate_reset()."""

    async def test_initiate_reset_returns_result_for_known_user(self):
        """A reset for a known active user returns PasswordResetResult with success=True."""
        service, _ = _make_service()

        result = await service.initiate_reset(user_id=_USER_ID, session_id=_SESSION_ID)

        assert result.success is True
        assert result.ticket_reference == "CHG1234567"
        assert result.delivery_method == "email"

    async def test_initiate_reset_records_session_action_on_success(self):
        """A successful reset records the action in SessionService."""
        service, session_service = _make_service()

        await service.initiate_reset(user_id=_USER_ID, session_id=_SESSION_ID)

        session = await session_service.get_session(_SESSION_ID)
        assert session is not None
        action_names = [a.action for a in session.actions]
        assert "password_reset_initiated" in action_names

    async def test_initiate_reset_raises_user_not_found_for_unknown_user(self):
        """A reset for an unknown user_id raises UserNotFoundError."""
        service, _ = _make_service()

        with pytest.raises(UserNotFoundError):
            await service.initiate_reset(user_id="unknown@acme.com", session_id=_SESSION_ID)

    async def test_initiate_reset_raises_password_reset_error_on_integration_failure(self):
        """An AD integration failure is converted to PasswordResetError, not IntegrationError."""
        service, _ = _make_service()

        with pytest.raises(PasswordResetError):
            await service.initiate_reset(user_id="error@acme.com", session_id=_SESSION_ID)

    async def test_session_action_not_recorded_on_failure(self):
        """Session action is not recorded when the reset fails."""
        service, session_service = _make_service()

        with pytest.raises(UserNotFoundError):
            await service.initiate_reset(user_id="unknown@acme.com", session_id=_SESSION_ID)

        session = await session_service.get_session(_SESSION_ID)
        assert session is None
