"""Unit tests for TicketService. Implemented in Phase 3d."""

from datetime import datetime, timezone

import pytest
import structlog

from app.core.exceptions import IntegrationError, TicketCreationError, TicketNotFoundError
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest
from app.services.business.session_service import SessionService
from app.services.business.ticket_service import TicketService

_SESSION_ID = "test-session-002"
_SEEDED_TICKET = IncidentResult(
    ticket_number="INC9990001",
    short_description="Test incident",
    state="In Progress",
    priority="3 - Moderate",
    assigned_to="IT Support Team",
    created_at=datetime(2026, 6, 30, 10, 0, 0, tzinfo=timezone.utc),
    caller_id="john.doe@acme.com",
)


class _StubServiceNowClient(BaseServiceNowClient):
    """Stub ServiceNow client with deterministic behaviour for testing."""

    def __init__(self) -> None:
        self.last_create_request: TicketCreateRequest | None = None

    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        self.last_create_request = request
        if request.caller_id == "error@acme.com":
            raise IntegrationError("ServiceNow unavailable")
        return IncidentResult(
            ticket_number="INC9990001",
            short_description=request.short_description,
            state="New",
            priority=request.priority,
            assigned_to="IT Support Queue",
            created_at=datetime(2026, 6, 30, 10, 0, 0, tzinfo=timezone.utc),
            caller_id=request.caller_id,
        )

    async def get_incident(self, ticket_number: str) -> IncidentResult:
        if ticket_number == "INC0000000":
            raise TicketNotFoundError(f"Ticket not found: {ticket_number}")
        return _SEEDED_TICKET


def _make_service() -> tuple[TicketService, SessionService, _StubServiceNowClient]:
    logger = structlog.get_logger()
    session_service = SessionService(logger=logger)
    stub = _StubServiceNowClient()
    service = TicketService(
        servicenow_client=stub,
        session_service=session_service,
        logger=logger,
    )
    return service, session_service, stub


def _make_request(**overrides) -> TicketCreateRequest:
    defaults = {
        "short_description": "Test incident",
        "description": "Detailed description.",
        "priority": "3 - Moderate",
        "category": "General",
        "caller_id": "john.doe@acme.com",
    }
    return TicketCreateRequest(**{**defaults, **overrides})


class TestTicketService:
    """Unit tests for TicketService.create_ticket() and get_ticket_status()."""

    async def test_create_ticket_returns_incident_result(self):
        """Creating a ticket returns an IncidentResult with a ticket number and state New."""
        service, _, _ = _make_service()

        result = await service.create_ticket(request=_make_request(), session_id=_SESSION_ID)

        assert result.state == "New"
        assert result.ticket_number == "INC9990001"

    async def test_create_ticket_records_session_action(self):
        """Successful ticket creation records the ticket_number in a session action."""
        service, session_service, _ = _make_service()

        result = await service.create_ticket(request=_make_request(), session_id=_SESSION_ID)

        session = await session_service.get_session(_SESSION_ID)
        assert session is not None
        ticket_action = next(
            (a for a in session.actions if a.action == "ticket_created"), None
        )
        assert ticket_action is not None
        assert ticket_action.metadata["ticket_number"] == result.ticket_number

    async def test_create_ticket_raises_on_servicenow_failure(self):
        """ServiceNow integration failure is converted to TicketCreationError."""
        service, _, _ = _make_service()

        with pytest.raises(TicketCreationError):
            await service.create_ticket(
                request=_make_request(caller_id="error@acme.com"), session_id=_SESSION_ID
            )

    async def test_get_ticket_status_returns_result_for_known_ticket(self):
        """Querying a known ticket number returns its current IncidentResult."""
        service, _, _ = _make_service()

        result = await service.get_ticket_status(
            ticket_number="INC9990001", session_id=_SESSION_ID
        )

        assert result.ticket_number == "INC9990001"
        assert result.state == "In Progress"

    async def test_get_ticket_status_raises_for_unknown_ticket(self):
        """Querying an unknown ticket number raises TicketNotFoundError."""
        service, _, _ = _make_service()

        with pytest.raises(TicketNotFoundError):
            await service.get_ticket_status(
                ticket_number="INC0000000", session_id=_SESSION_ID
            )
