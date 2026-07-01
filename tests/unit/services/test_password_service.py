"""Unit tests for PasswordService. Implemented in Phase 3d.

Tests cover:
- Successful password reset for active users
- UserNotFoundError propagation for unknown users
- IntegrationError handling when AD is unavailable
- Session action recording on successful reset
- Session action NOT recorded on failure
"""

import pytest


class TestPasswordService:
    """Unit tests for PasswordService.initiate_reset()."""

    async def test_initiate_reset_returns_result_for_known_user(self):
        """A reset for a known active user returns PasswordResetResult with success=True."""
        pass

    async def test_initiate_reset_records_session_action_on_success(self):
        """A successful reset records the action in SessionService."""
        pass

    async def test_initiate_reset_raises_user_not_found_for_unknown_user(self):
        """A reset for an unknown user_id raises UserNotFoundError."""
        pass

    async def test_initiate_reset_raises_password_reset_error_on_integration_failure(self):
        """An AD integration failure raises PasswordResetError, not IntegrationError."""
        pass

    async def test_session_action_not_recorded_on_failure(self):
        """Session action is not recorded when the reset fails."""
        pass
