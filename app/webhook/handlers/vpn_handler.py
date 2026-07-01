"""VPN troubleshooting webhook handler. Implemented in Phase 3d."""

import structlog

from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.business.vpn_service import VPNService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class VPNHandler(BaseHandler):
    """Handles the it.vpn.troubleshoot intent."""

    def __init__(
        self,
        vpn_service: VPNService,
        response_builder: ResponseBuilder,
        logger: structlog.BoundLogger,
    ) -> None:
        self.vpn_service = vpn_service
        self.response_builder = response_builder
        self.logger = logger.bind(handler="VPNHandler")

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle VPN troubleshooting intent fulfillment."""
        ...
