"""Unit tests for EscalationService. Implemented in Phase 3d."""

from datetime import datetime, timezone

import pytest
import structlog

from app.core.exceptions import EscalationError, IntegrationError
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest
from app.services.business.escalation_service import EscalationService
from app.services.business.session_service import SessionService

_SESSION_ID = "test-session-004"
_USER_ID = "john.doe@acme.com"


class _StubServiceNowClient(BaseServiceNowClient):
    """Stub ServiceNow client that captures the create request for assertions."""

    def __init__(self) -> None:
        self.last_create_request: TicketCreateRequest | None = None

    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        self.last_create_request = request
        if request.caller_id == "error@acme.com":
            raise IntegrationError("ServiceNow unavailable")
        return IncidentResult(
            ticket_number="INC9880001",
            short_description=request.short_description,
            state="New",
            priority=request.priority,
            assigned_to="IT Support Queue",
            created_at=datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc),
            caller_id=request.caller_id,
        )

    async def get_incident(self, ticket_number: str) -> IncidentResult:
        raise NotImplementedError("Not called by EscalationService")


def _make_service() -> tuple[EscalationService, SessionService, _StubServiceNowClient]:
    logger = structlog.get_logger()
    session_service = SessionService(logger=logger)
    stub = _StubServiceNowClient()
    service = EscalationService(
        servicenow_client=stub,
        session_service=session_service,
        logger=logger,
    )
    return service, session_service, stub


class TestEscalationService:
    """Unit tests for EscalationService.escalate()."""

    async def test_escalate_returns_queue_info(self):
        """escalate() returns a dict with queue_position, estimated_wait_minutes, escalation_ticket."""
        service, _, _ = _make_service()

        result = await service.escalate(
            user_id=_USER_ID, session_id=_SESSION_ID, reason="Cannot resolve VPN issue"
        )

        assert "queue_position" in result
        assert "estimated_wait_minutes" in result
        assert "escalation_ticket" in result
        assert result["escalation_ticket"] == "INC9880001"
        assert isinstance(result["queue_position"], int)
        assert isinstance(result["estimated_wait_minutes"], int)

    async def test_escalate_creates_high_priority_ticket(self):
        """escalate() creates a ServiceNow incident with priority '2 - High'."""
        service, _, stub = _make_service()

        await service.escalate(
            user_id=_USER_ID, session_id=_SESSION_ID, reason="Complex VPN failure"
        )

        assert stub.last_create_request is not None
        assert stub.last_create_request.priority == "2 - High"
        assert stub.last_create_request.caller_id == _USER_ID

    async def test_escalate_records_session_action(self):
        """escalate() records the 'escalated_to_human' action in SessionService."""
        service, session_service, _ = _make_service()

        await service.escalate(
            user_id=_USER_ID, session_id=_SESSION_ID, reason="Need human assistance"
        )

        session = await session_service.get_session(_SESSION_ID)
        assert session is not None
        action_names = [a.action for a in session.actions]
        assert "escalated_to_human" in action_names

    async def test_escalate_raises_escalation_error_on_failure(self):
        """An IntegrationError from ServiceNow is converted to EscalationError."""
        service, _, _ = _make_service()

        with pytest.raises(EscalationError):
            await service.escalate(
                user_id="error@acme.com", session_id=_SESSION_ID, reason="Test escalation"
            )
