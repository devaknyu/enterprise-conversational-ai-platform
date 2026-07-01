"""Unit tests for MockServiceNowClient. Implemented in Phase 3c."""

import pytest

from app.core.exceptions import IntegrationError, TicketNotFoundError
from app.integrations.servicenow.mock import MockServiceNowClient
from app.models.ticket import TicketCreateRequest


def _make_client(error_rate: float = 0.0) -> MockServiceNowClient:
    """Instantiate client with zero latency for fast tests."""
    return MockServiceNowClient(
        error_rate=error_rate,
        latency_min_ms=0,
        latency_max_ms=0,
    )


def _make_request(**overrides) -> TicketCreateRequest:
    defaults = {
        "short_description": "Test incident",
        "description": "Detailed description of the test incident.",
        "priority": "3 - Moderate",
        "category": "General",
        "caller_id": "john.doe@acme.com",
    }
    return TicketCreateRequest(**{**defaults, **overrides})


class TestMockServiceNowClient:
    """Unit tests for MockServiceNowClient."""

    async def test_create_incident_returns_new_ticket(self):
        """create_incident returns an IncidentResult with state 'New' and an INC ticket number."""
        client = _make_client()

        result = await client.create_incident(_make_request())

        assert result.state == "New"
        assert result.ticket_number.startswith("INC")
        assert len(result.ticket_number) == 10  # INC + 7 digits

    async def test_create_incident_preserves_caller_id(self):
        """create_incident propagates caller_id from the request to the result."""
        client = _make_client()

        result = await client.create_incident(_make_request(caller_id="jane.smith@acme.com"))

        assert result.caller_id == "jane.smith@acme.com"

    async def test_get_incident_returns_known_ticket(self):
        """get_incident returns the seeded IncidentResult for a known ticket number."""
        client = _make_client()

        result = await client.get_incident("INC0001234")

        assert result.ticket_number == "INC0001234"
        assert result.state == "In Progress"
        assert result.priority == "2 - High"

    async def test_get_incident_raises_ticket_not_found(self):
        """get_incident raises TicketNotFoundError for an unknown ticket number."""
        client = _make_client()

        with pytest.raises(TicketNotFoundError):
            await client.get_incident("INC9999999")

    async def test_simulated_error_raises_integration_error(self):
        """When error_rate=1.0 every call raises IntegrationError."""
        client = _make_client(error_rate=1.0)

        with pytest.raises(IntegrationError):
            await client.create_incident(_make_request())
