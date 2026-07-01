"""Mock ServiceNow client for development and testing. Implemented in Phase 3c."""

import asyncio
import random
from datetime import datetime, timezone

import structlog

from app.core.exceptions import IntegrationError, TicketNotFoundError
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest

_MOCK_TICKETS: dict[str, IncidentResult] = {
    "INC0001234": IncidentResult(
        ticket_number="INC0001234",
        short_description="VPN connectivity failure",
        state="In Progress",
        priority="2 - High",
        assigned_to="IT Support Team",
        created_at=datetime(2026, 6, 28, 9, 0, 0, tzinfo=timezone.utc),
        caller_id="john.doe@acme.com",
    ),
    "INC0001235": IncidentResult(
        ticket_number="INC0001235",
        short_description="Software installation request",
        state="Open",
        priority="3 - Moderate",
        assigned_to="IT Support Team",
        created_at=datetime(2026, 6, 29, 14, 30, 0, tzinfo=timezone.utc),
        caller_id="jane.smith@acme.com",
    ),
}


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

    async def _simulate_call(self, operation: str) -> None:
        """Inject configurable latency and a random transient failure."""
        delay = random.uniform(self.latency_min_ms, self.latency_max_ms) / 1000
        await asyncio.sleep(delay)
        if random.random() < self.error_rate:
            self.logger.warning("mock_error_injected", operation=operation)
            raise IntegrationError(
                f"ServiceNow unavailable (simulated failure in {operation})"
            )

    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        """Simulate incident creation with latency and configurable error rate."""
        await self._simulate_call("create_incident")
        ticket_number = f"INC{random.randint(1000000, 9999999)}"
        result = IncidentResult(
            ticket_number=ticket_number,
            short_description=request.short_description,
            state="New",
            priority=request.priority,
            assigned_to="IT Support Queue",
            created_at=datetime.now(timezone.utc),
            caller_id=request.caller_id,
        )
        self.logger.info(
            "sn_create_incident",
            ticket_number=ticket_number,
            caller_id=request.caller_id,
        )
        return result

    async def get_incident(self, ticket_number: str) -> IncidentResult:
        """Simulate incident retrieval with latency and configurable error rate."""
        await self._simulate_call("get_incident")
        if ticket_number not in _MOCK_TICKETS:
            raise TicketNotFoundError(f"Ticket not found: {ticket_number}")
        ticket = _MOCK_TICKETS[ticket_number]
        self.logger.info(
            "sn_get_incident", ticket_number=ticket_number, state=ticket.state
        )
        return ticket
