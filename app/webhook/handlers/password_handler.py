"""Password reset webhook handler. Implemented in Phase 3d."""

import structlog

from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.business.password_service import PasswordService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class PasswordHandler(BaseHandler):
    """Handles the it.password.reset intent.

    Extracts user_email from session parameters, delegates to PasswordService,
    and formats the fulfillment response via ResponseBuilder.
    """

    def __init__(
        self,
        password_service: PasswordService,
        response_builder: ResponseBuilder,
        logger: structlog.BoundLogger,
    ) -> None:
        self.password_service = password_service
        self.response_builder = response_builder
        self.logger = logger.bind(handler="PasswordHandler")

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle it.password.reset intent fulfillment."""
        ...
