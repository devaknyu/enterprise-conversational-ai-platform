"""Mock ServiceNow client for development and testing. Implemented in Phase 3c."""

import structlog

from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest


class MockServiceNowClient(BaseServiceNowClient):
    """Mock ServiceNow client with realistic latency and error simulation.

    Available test tickets:
        INC0001234 — In Progress, VPN issue, high priority
        INC0001235 — Open, software install, moderate priority
    """

    def __init__(
        self,
        error_rate: float = 0.05,
        latency_min_ms: int = 100,
        latency_max_ms: int = 300,
    ) -> None:
        self.error_rate = error_rate
        self.latency_min_ms = latency_min_ms
        self.latency_max_ms = latency_max_ms
        self.logger = structlog.get_logger(__name__).bind(client="MockServiceNowClient")

    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        """Simulate incident creation with latency and configurable error rate."""
        ...

    async def get_incident(self, ticket_number: str) -> IncidentResult:
        """Simulate incident retrieval with latency and configurable error rate."""
        ...
