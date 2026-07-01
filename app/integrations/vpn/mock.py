"""Mock VPN gateway client for development and testing. Implemented in Phase 3c."""

import asyncio
import random

import structlog

from app.core.exceptions import IntegrationError, VPNServiceError
from app.integrations.vpn.base import BaseVPNClient

_MOCK_VPN_STATUS: dict[str, dict] = {
    "john.doe@acme.com": {
        "connected": True,
        "last_connected": "2026-06-30T08:00:00Z",
        "client_version": "5.0.2",
        "assigned_ip": "10.8.0.101",
    },
    "jane.smith@acme.com": {
        "connected": False,
        "last_connected": "2026-06-29T17:30:00Z",
        "client_version": "5.0.1",
        "assigned_ip": None,
    },
    "bob.jones@acme.com": {
        "connected": False,
        "last_connected": "2026-06-28T12:00:00Z",
        "client_version": "4.9.8",
        "assigned_ip": None,
    },
}

_DEFAULT_VPN_STATUS: dict = {
    "connected": False,
    "last_connected": None,
    "client_version": "unknown",
    "assigned_ip": None,
}

_CHECKS_CONNECTED = [
    {"name": "dns_resolution", "status": "pass"},
    {"name": "tunnel_establishment", "status": "pass"},
    {"name": "latency_check", "status": "pass"},
]

_CHECKS_DISCONNECTED = [
    {"name": "dns_resolution", "status": "pass"},
    {"name": "tunnel_establishment", "status": "fail"},
    {"name": "latency_check", "status": "skipped"},
]


class MockVPNClient(BaseVPNClient):
    """Mock VPN gateway client with realistic latency and error simulation."""

    def __init__(
        self,
        error_rate: float = 0.05,
        latency_min_ms: int = 100,
        latency_max_ms: int = 300,
    ) -> None:
        self.error_rate = error_rate
        self.latency_min_ms = latency_min_ms
        self.latency_max_ms = latency_max_ms
        self.logger = structlog.get_logger(__name__).bind(client="MockVPNClient")

    async def _simulate_call(self, operation: str) -> None:
        """Inject configurable latency and a random transient failure."""
        delay = random.uniform(self.latency_min_ms, self.latency_max_ms) / 1000
        await asyncio.sleep(delay)
        if random.random() < self.error_rate:
            self.logger.warning("mock_error_injected", operation=operation)
            raise VPNServiceError(
                f"VPN gateway unavailable (simulated failure in {operation})"
            )

    async def get_connection_status(self, user_id: str) -> dict:
        """Simulate VPN status retrieval with latency and configurable error rate."""
        await self._simulate_call("get_connection_status")
        status = _MOCK_VPN_STATUS.get(user_id, _DEFAULT_VPN_STATUS)
        self.logger.info(
            "vpn_get_status", user_id=user_id, connected=status["connected"]
        )
        return status

    async def run_diagnostics(self, user_id: str) -> dict:
        """Simulate VPN diagnostics with latency and configurable error rate."""
        await self._simulate_call("run_diagnostics")
        status = _MOCK_VPN_STATUS.get(user_id, _DEFAULT_VPN_STATUS)
        connected = status["connected"]
        if connected:
            issues: list[str] = []
            recommended_actions: list[str] = []
            checks = _CHECKS_CONNECTED
        else:
            issues = ["VPN tunnel could not be established"]
            recommended_actions = [
                "Reinstall VPN client",
                "Contact IT support if issue persists",
            ]
            checks = _CHECKS_DISCONNECTED
        self.logger.info(
            "vpn_run_diagnostics", user_id=user_id, issue_count=len(issues)
        )
        return {
            "checks": checks,
            "issues": issues,
            "recommended_actions": recommended_actions,
        }
