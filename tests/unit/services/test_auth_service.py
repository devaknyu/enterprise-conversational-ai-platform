"""Unit tests for AuthService. Implemented in Phase 3b."""

import pytest

from app.core.exceptions import IntegrationError, UserNotFoundError
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult, UserProfile
from app.services.business.auth_service import AuthService
from app.services.business.session_service import SessionService

_SESSION_ID = "projects/test/locations/us-central1/agents/ag/sessions/sess-001"

_KNOWN_USER = UserProfile(
    user_id="john.doe@acme.com",
    employee_id="EMP001",
    display_name="John Doe",
    email="john.doe@acme.com",
    department="Engineering",
    manager="jane.smith@acme.com",
    phone="+1-555-0100",
    location="NYC",
    account_status="active",
)


class _StubADClient(BaseActiveDirectoryClient):
    """Minimal AD client stub for AuthService tests."""

    def __init__(self, users: dict[str, UserProfile]) -> None:
        self._users = users

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Return profile or raise UserNotFoundError."""
        if user_id not in self._users:
            raise UserNotFoundError(f"User not found: {user_id}")
        return self._users[user_id]

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        """Not used by AuthService — required by abstract base."""
        raise NotImplementedError


class _FailingADClient(BaseActiveDirectoryClient):
    """AD client stub that simulates a service outage."""

    async def get_user_profile(self, user_id: str) -> UserProfile:
        raise IntegrationError("AD service unavailable")

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        raise NotImplementedError


def _make_auth_service(ad_client: BaseActiveDirectoryClient, test_logger) -> AuthService:
    session_svc = SessionService(logger=test_logger)
    return AuthService(ad_client=ad_client, session_service=session_svc, logger=test_logger)


class TestAuthService:
    """Unit tests for AuthService.verify_user()."""

    async def test_verify_user_returns_profile_for_known_user(self, test_logger):
        """verify_user() returns the UserProfile for a user that exists in AD."""
        ad = _StubADClient({"john.doe@acme.com": _KNOWN_USER})
        svc = _make_auth_service(ad, test_logger)

        profile = await svc.verify_user("john.doe@acme.com", _SESSION_ID)

        assert profile.user_id == "john.doe@acme.com"
        assert profile.department == "Engineering"

    async def test_verify_user_raises_user_not_found_for_unknown_user(self, test_logger):
        """verify_user() propagates UserNotFoundError when the user is absent from AD."""
        ad = _StubADClient({})
        svc = _make_auth_service(ad, test_logger)

        with pytest.raises(UserNotFoundError):
            await svc.verify_user("unknown@acme.com", _SESSION_ID)

    async def test_verify_user_records_session_action_on_success(self, test_logger):
        """Successful verify_user() records a 'user_verified' action in the session."""
        ad = _StubADClient({"john.doe@acme.com": _KNOWN_USER})
        session_svc = SessionService(logger=test_logger)
        svc = AuthService(ad_client=ad, session_service=session_svc, logger=test_logger)

        await svc.verify_user("john.doe@acme.com", _SESSION_ID)

        state = await session_svc.get_session(_SESSION_ID)
        assert state is not None
        assert any(a.action == "user_verified" for a in state.actions)

    async def test_verify_user_propagates_integration_error(self, test_logger):
        """verify_user() propagates IntegrationError when AD is unavailable."""
        svc = _make_auth_service(_FailingADClient(), test_logger)

        with pytest.raises(IntegrationError):
            await svc.verify_user("john.doe@acme.com", _SESSION_ID)
