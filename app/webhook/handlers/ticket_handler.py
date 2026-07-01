"""IT ticket webhook handler."""

import structlog

from app.core.exceptions import IntegrationError, TicketCreationError, TicketNotFoundError
from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.models.ticket import TicketCreateRequest
from app.services.business.ticket_service import TicketService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class TicketHandler(BaseHandler):
    """Handles it.ticket.create and it.ticket.status intents.

    Branches on fulfillment_info.tag ('create' vs 'status') so a single
    handler instance can be registered under both intent names.
    """

    def __init__(
        self,
        ticket_service: TicketService,
        response_builder: ResponseBuilder,
        logger: structlog.BoundLogger,
    ) -> None:
        self.ticket_service = ticket_service
        self.response_builder = response_builder
        self.logger = logger.bind(handler="TicketHandler")

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle ticket creation or status query based on fulfillment tag.

        Args:
            request: Parsed Dialogflow webhook request. fulfillment_info.tag
                     must be 'create' or 'status'.

        Returns:
            WebhookResponse confirming ticket creation or reporting current status.

        Raises:
            MissingParameterError: If required parameters are absent for the tag action.
        """
        tag = request.fulfillment_info.tag
        session_id = request.session_info.session

        if tag == "create":
            return await self._handle_create(request, session_id)
        if tag == "status":
            return await self._handle_status(request, session_id)

        self.logger.warning("ticket_handler_unknown_tag", tag=tag)
        return self.response_builder.build_error_response(
            "I'm not sure what you need for your ticket. Please try again."
        )

    async def _handle_create(self, request: WebhookRequest, session_id: str) -> WebhookResponse:
        """Create a new ServiceNow incident from the session parameters."""
        caller_id: str = self._require_param(request, "caller_id")
        short_description: str = self._require_param(request, "short_description")
        category: str = self._get_param(request, "category", "General")

        ticket_request = TicketCreateRequest(
            short_description=short_description,
            description=short_description,
            category=category,
            caller_id=caller_id,
        )

        self.logger.info("ticket_create_handling", caller_id=caller_id, session_id=session_id)

        try:
            result = await self.ticket_service.create_ticket(ticket_request, session_id)
        except TicketCreationError as exc:
            self.logger.error("ticket_handler_creation_error", error=str(exc))
            return self.response_builder.build_error_response(
                "I was unable to create a ticket at this time. Please try again or contact IT directly."
            )

        return self.response_builder.build_ticket_created_response(result)

    async def _handle_status(self, request: WebhookRequest, session_id: str) -> WebhookResponse:
        """Retrieve the current status of an existing ServiceNow incident."""
        ticket_number: str = self._require_param(request, "ticket_number")

        self.logger.info("ticket_status_handling", ticket_number=ticket_number, session_id=session_id)

        try:
            result = await self.ticket_service.get_ticket_status(ticket_number, session_id)
        except TicketNotFoundError:
            return self.response_builder.build_error_response(
                f"Ticket {ticket_number} was not found. Please verify the ticket number."
            )
        except IntegrationError as exc:
            self.logger.error("ticket_handler_status_error", error=str(exc))
            return self.response_builder.build_error_response(
                "Unable to retrieve ticket status at this time. Please try again."
            )

        return self.response_builder.build_ticket_status_response(result)
