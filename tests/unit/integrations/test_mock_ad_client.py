"""Unit tests for MockActiveDirectoryClient. Implemented in Phase 3c."""

import pytest

from app.core.exceptions import IntegrationError, UserNotFoundError
from app.integrations.active_directory.mock import MockActiveDirectoryClient
from app.models.ticket import TicketCreateRequest


def _make_client(error_rate: float = 0.0) -> MockActiveDirectoryClient:
    """Instantiate client with zero latency for fast tests."""
    return MockActiveDirectoryClient(
        error_rate=error_rate,
        latency_min_ms=0,
        latency_max_ms=0,
    )


class TestMockActiveDirectoryClient:
    """Unit tests for MockActiveDirectoryClient."""

    async def test_get_user_profile_returns_known_user(self):
        """get_user_profile returns a fully populated UserProfile for a known user."""
        client = _make_client()

        profile = await client.get_user_profile("john.doe@acme.com")

        assert profile.user_id == "john.doe@acme.com"
        assert profile.department == "Engineering"
        assert profile.account_status == "active"

    async def test_get_user_profile_returns_locked_user_profile(self):
        """get_user_profile returns the profile for a locked account without raising."""
        client = _make_client()

        profile = await client.get_user_profile("bob.jones@acme.com")

        assert profile.user_id == "bob.jones@acme.com"
        assert profile.account_status == "locked"

    async def test_get_user_profile_raises_user_not_found_for_unknown_user(self):
        """get_user_profile raises UserNotFoundError for a user absent from the dataset."""
        client = _make_client()

        with pytest.raises(UserNotFoundError):
            await client.get_user_profile("unknown@acme.com")

    async def test_reset_password_returns_success_for_known_user(self):
        """reset_password returns a PasswordResetResult with success=True and a CHG reference."""
        client = _make_client()

        result = await client.reset_password("john.doe@acme.com")

        assert result.success is True
        assert result.user_id == "john.doe@acme.com"
        assert result.ticket_reference.startswith("CHG")
        assert result.delivery_method == "email"

    async def test_reset_password_raises_user_not_found_for_unknown_user(self):
        """reset_password raises UserNotFoundError for a user absent from the dataset."""
        client = _make_client()

        with pytest.raises(UserNotFoundError):
            await client.reset_password("unknown@acme.com")

    async def test_simulated_error_raises_integration_error(self):
        """When error_rate=1.0 every call raises IntegrationError."""
        client = _make_client(error_rate=1.0)

        with pytest.raises(IntegrationError):
            await client.get_user_profile("john.doe@acme.com")
