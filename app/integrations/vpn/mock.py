"""Mock VPN gateway client for development and testing. Implemented in Phase 3c."""

import structlog

from app.integrations.vpn.base import BaseVPNClient


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

    async def get_connection_status(self, user_id: str) -> dict:
        """Simulate VPN status retrieval with latency and configurable error rate."""
        ...

    async def run_diagnostics(self, user_id: str) -> dict:
        """Simulate VPN diagnostics with latency and configurable error rate."""
        ...
