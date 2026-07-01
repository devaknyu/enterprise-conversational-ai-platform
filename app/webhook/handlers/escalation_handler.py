"""Human escalation webhook handler."""

import structlog

from app.core.exceptions import EscalationError
from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.business.escalation_service import EscalationService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder

_DEFAULT_REASON = "Employee requested escalation to human agent"


class EscalationHandler(BaseHandler):
    """Handles the it.escalate intent."""

    def __init__(
        self,
        escalation_service: EscalationService,
        response_builder: ResponseBuilder,
        logger: structlog.BoundLogger,
    ) -> None:
        self.escalation_service = escalation_service
        self.response_builder = response_builder
        self.logger = logger.bind(handler="EscalationHandler")

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle escalation to human agent intent fulfillment.

        Args:
            request: Parsed Dialogflow webhook request. Expects user_id in session
                     parameters and optionally a reason string.

        Returns:
            WebhookResponse confirming escalation with queue position and wait estimate.

        Raises:
            MissingParameterError: If user_id is absent from request parameters.
        """
        user_id: str = self._require_param(request, "user_id")
        session_id: str = request.session_info.session
        reason: str = self._get_param(request, "reason", _DEFAULT_REASON)

        self.logger.info("escalation_handler_handling", user_id=user_id, session_id=session_id)

        try:
            result = await self.escalation_service.escalate(
                user_id=user_id,
                session_id=session_id,
                reason=reason,
            )
        except EscalationError as exc:
            self.logger.error("escalation_handler_error", user_id=user_id, error=str(exc))
            return self.response_builder.build_error_response(
                "I was unable to reach the IT support queue at this time. Please call IT directly."
            )

        return self.response_builder.build_escalation_response(
            result["queue_position"],
            result["estimated_wait_minutes"],
        )
