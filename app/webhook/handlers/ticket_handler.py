"""IT ticket webhook handler. Implemented in Phase 3d."""

import structlog

from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.business.ticket_service import TicketService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class TicketHandler(BaseHandler):
    """Handles it.ticket.create and it.ticket.status intents."""

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
        """Handle ticket creation or status query based on fulfillment tag."""
        ...
