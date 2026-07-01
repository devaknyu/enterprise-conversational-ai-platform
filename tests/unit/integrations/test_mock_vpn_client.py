"""Unit tests for MockVPNClient. Implemented in Phase 3c."""

import pytest

from app.core.exceptions import VPNServiceError
from app.integrations.vpn.mock import MockVPNClient


def _make_client(error_rate: float = 0.0) -> MockVPNClient:
    """Instantiate client with zero latency for fast tests."""
    return MockVPNClient(
        error_rate=error_rate,
        latency_min_ms=0,
        latency_max_ms=0,
    )


class TestMockVPNClient:
    """Unit tests for MockVPNClient."""

    async def test_get_connection_status_connected_user(self):
        """get_connection_status returns connected=True for a user with an active VPN session."""
        client = _make_client()

        status = await client.get_connection_status("john.doe@acme.com")

        assert status["connected"] is True
        assert status["assigned_ip"] == "10.8.0.101"

    async def test_get_connection_status_disconnected_user(self):
        """get_connection_status returns connected=False for a user with no active session."""
        client = _make_client()

        status = await client.get_connection_status("jane.smith@acme.com")

        assert status["connected"] is False
        assert status["assigned_ip"] is None

    async def test_get_connection_status_unknown_user_returns_default(self):
        """get_connection_status returns a default disconnected status for unenrolled users."""
        client = _make_client()

        status = await client.get_connection_status("unenrolled@acme.com")

        assert status["connected"] is False
        assert status["client_version"] == "unknown"

    async def test_run_diagnostics_no_issues_for_connected_user(self):
        """run_diagnostics reports no issues when the user has an active VPN connection."""
        client = _make_client()

        result = await client.run_diagnostics("john.doe@acme.com")

        assert result["issues"] == []
        assert result["recommended_actions"] == []
        assert all(c["status"] == "pass" for c in result["checks"])

    async def test_run_diagnostics_issues_for_disconnected_user(self):
        """run_diagnostics reports tunnel failure and recommended actions when disconnected."""
        client = _make_client()

        result = await client.run_diagnostics("jane.smith@acme.com")

        assert len(result["issues"]) > 0
        assert len(result["recommended_actions"]) > 0
        tunnel_check = next(c for c in result["checks"] if c["name"] == "tunnel_establishment")
        assert tunnel_check["status"] == "fail"

    async def test_simulated_error_raises_vpn_service_error(self):
        """When error_rate=1.0 every call raises VPNServiceError."""
        client = _make_client(error_rate=1.0)

        with pytest.raises(VPNServiceError):
            await client.get_connection_status("john.doe@acme.com")
