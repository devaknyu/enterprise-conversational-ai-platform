"""Unit tests for TicketHandler."""

from datetime import datetime, timezone

import pytest

from app.core.exceptions import IntegrationError, MissingParameterError, TicketCreationError, TicketNotFoundError
from app.models.dialogflow import FulfillmentInfo, SessionInfo, WebhookRequest
from app.models.ticket import IncidentResult, TicketCreateRequest
from app.webhook.handlers.ticket_handler import TicketHandler
from app.webhook.response_builder import ResponseBuilder


def _make_request(tag: str, **params) -> WebhookRequest:
    return WebhookRequest(
        fulfillment_info=FulfillmentInfo(tag=tag),
        session_info=SessionInfo(session="sess-001", parameters=params),
    )


def _incident(**kwargs) -> IncidentResult:
    defaults = dict(
        ticket_number="INC0001234",
        short_description="VPN connectivity issue",
        state="New",
        priority="3 - Moderate",
        assigned_to="IT Support Queue",
        created_at=datetime.now(tz=timezone.utc),
        caller_id="john.doe@acme.com",
    )
    defaults.update(kwargs)
    return IncidentResult(**defaults)


class _MockTicketService:
    def __init__(
        self,
        create_result: IncidentResult | None = None,
        status_result: IncidentResult | None = None,
        raises: Exception | None = None,
    ):
        self._create_result = create_result
        self._status_result = status_result
        self._raises = raises

    async def create_ticket(self, request: TicketCreateRequest, session_id: str) -> IncidentResult:
        """Return fixture result or raise configured exception."""
        if self._raises:
            raise self._raises
        return self._create_result  # type: ignore[return-value]

    async def get_ticket_status(self, ticket_number: str, session_id: str) -> IncidentResult:
        """Return fixture result or raise configured exception."""
        if self._raises:
            raise self._raises
        return self._status_result  # type: ignore[return-value]


class TestTicketHandler:
    """Unit tests for TicketHandler.handle()."""

    async def test_handle_create_returns_confirmation_with_ticket_number(self, test_logger):
        """Tag='create' calls create_ticket and returns a message with the ticket number."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(create_result=_incident()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        request = _make_request("create", caller_id="john.doe@acme.com", short_description="VPN issue")
        response = await handler.handle(request)
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "INC0001234" in text

    async def test_handle_status_returns_current_ticket_state(self, test_logger):
        """Tag='status' calls get_ticket_status and reports the ticket state."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(status_result=_incident(state="In Progress")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        request = _make_request("status", ticket_number="INC0001234")
        response = await handler.handle(request)
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "INC0001234" in text
        assert "In Progress" in text

    async def test_handle_missing_caller_id_on_create_raises_missing_param(self, test_logger):
        """MissingParameterError raised when caller_id is absent for create."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(create_result=_incident()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        with pytest.raises(MissingParameterError):
            await handler.handle(_make_request("create", short_description="issue"))

    async def test_handle_missing_ticket_number_on_status_raises_missing_param(self, test_logger):
        """MissingParameterError raised when ticket_number is absent for status."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(status_result=_incident()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        with pytest.raises(MissingParameterError):
            await handler.handle(_make_request("status"))

    async def test_handle_ticket_creation_error_returns_error_response(self, test_logger):
        """TicketCreationError is caught and returns a user-friendly error message."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(raises=TicketCreationError("ServiceNow down")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(
            _make_request("create", caller_id="john.doe@acme.com", short_description="VPN issue")
        )
        text = response.fulfillment_response.messages[0].text.text[0]
        assert len(text) > 0

    async def test_handle_ticket_not_found_returns_not_found_message(self, test_logger):
        """TicketNotFoundError returns a response mentioning the ticket number."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(raises=TicketNotFoundError("INC9999999")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request("status", ticket_number="INC9999999"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "INC9999999" in text

    async def test_handle_unknown_tag_returns_error_response(self, test_logger):
        """Unknown fulfillment tag returns an error response rather than raising."""
        handler = TicketHandler(
            ticket_service=_MockTicketService(create_result=_incident()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request("delete"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert len(text) > 0
