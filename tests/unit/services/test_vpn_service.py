"""Unit tests for VPNService. Implemented in Phase 3d."""

import pytest
import structlog

from app.core.exceptions import VPNServiceError
from app.integrations.vpn.base import BaseVPNClient
from app.services.business.session_service import SessionService
from app.services.business.vpn_service import VPNService

_SESSION_ID = "test-session-003"

_CONNECTED_STATUS = {"connected": True, "last_connected": "2026-06-30T08:00:00Z",
                     "client_version": "5.0.2", "assigned_ip": "10.8.0.101"}
_CONNECTED_DIAGNOSTICS = {"checks": [{"name": "dns_resolution", "status": "pass"},
                                      {"name": "tunnel_establishment", "status": "pass"}],
                           "issues": [], "recommended_actions": []}

_DISCONNECTED_STATUS = {"connected": False, "last_connected": "2026-06-29T17:30:00Z",
                        "client_version": "5.0.1", "assigned_ip": None}
_DISCONNECTED_DIAGNOSTICS = {"checks": [{"name": "dns_resolution", "status": "pass"},
                                         {"name": "tunnel_establishment", "status": "fail"}],
                              "issues": ["VPN tunnel could not be established"],
                              "recommended_actions": ["Reinstall VPN client",
                                                      "Contact IT support if issue persists"]}


class _StubVPNClient(BaseVPNClient):
    """Stub VPN client. 'connected@acme.com' is connected; anything else is disconnected."""

    def __init__(self, raise_error: bool = False) -> None:
        self.raise_error = raise_error

    async def get_connection_status(self, user_id: str) -> dict:
        if self.raise_error:
            raise VPNServiceError("VPN gateway unavailable")
        return _CONNECTED_STATUS if user_id == "connected@acme.com" else _DISCONNECTED_STATUS

    async def run_diagnostics(self, user_id: str) -> dict:
        if self.raise_error:
            raise VPNServiceError("VPN gateway unavailable")
        return _CONNECTED_DIAGNOSTICS if user_id == "connected@acme.com" else _DISCONNECTED_DIAGNOSTICS


def _make_service(raise_error: bool = False) -> tuple[VPNService, SessionService]:
    logger = structlog.get_logger()
    session_service = SessionService(logger=logger)
    service = VPNService(
        vpn_client=_StubVPNClient(raise_error=raise_error),
        session_service=session_service,
        logger=logger,
    )
    return service, session_service


class TestVPNService:
    """Unit tests for VPNService.diagnose()."""

    async def test_diagnose_returns_structured_result(self):
        """Diagnosing a connected user returns the expected dict shape with escalate=False."""
        service, _ = _make_service()

        result = await service.diagnose(
            user_id="connected@acme.com", session_id=_SESSION_ID, symptoms=[]
        )

        assert "diagnosis" in result
        assert "steps" in result
        assert "escalate" in result
        assert result["escalate"] is False
        assert result["steps"] == []

    async def test_diagnose_sets_escalate_true_for_unresolvable_issues(self):
        """Diagnosing a disconnected user returns escalate=True and non-empty steps."""
        service, _ = _make_service()

        result = await service.diagnose(
            user_id="disconnected@acme.com", session_id=_SESSION_ID, symptoms=["cannot connect"]
        )

        assert result["escalate"] is True
        assert len(result["steps"]) > 0

    async def test_diagnose_raises_on_vpn_gateway_failure(self):
        """A VPN gateway failure propagates as VPNServiceError."""
        service, _ = _make_service(raise_error=True)

        with pytest.raises(VPNServiceError):
            await service.diagnose(
                user_id="any@acme.com", session_id=_SESSION_ID, symptoms=[]
            )
