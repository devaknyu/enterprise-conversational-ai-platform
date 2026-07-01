"""VPN troubleshooting webhook handler."""

import structlog

from app.core.exceptions import IntegrationError, VPNServiceError
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
        """Handle VPN troubleshooting intent fulfillment.

        Args:
            request: Parsed Dialogflow webhook request. Expects user_id in session
                     parameters and optionally a symptoms list entity.

        Returns:
            WebhookResponse with diagnosis and remediation steps. If VPN diagnostics
            indicate escalation is needed, includes an advisory to contact IT.

        Raises:
            MissingParameterError: If user_id is absent from request parameters.
        """
        user_id: str = self._require_param(request, "user_id")
        session_id: str = request.session_info.session
        symptoms = self._get_param(request, "symptoms", [])
        if not isinstance(symptoms, list):
            symptoms = [symptoms]

        self.logger.info(
            "vpn_handler_handling",
            user_id=user_id,
            session_id=session_id,
            symptom_count=len(symptoms),
        )

        try:
            result = await self.vpn_service.diagnose(
                user_id=user_id,
                session_id=session_id,
                symptoms=symptoms,
            )
        except (VPNServiceError, IntegrationError) as exc:
            self.logger.error("vpn_handler_error", user_id=user_id, error=str(exc))
            return self.response_builder.build_error_response(
                "VPN diagnostics are temporarily unavailable. Please contact IT support directly."
            )

        diagnosis: str = result["diagnosis"]
        steps: list[str] = result["steps"]

        if result["escalate"]:
            return self.response_builder.build_vpn_escalation_response(diagnosis, steps)
        return self.response_builder.build_vpn_response(diagnosis, steps)
