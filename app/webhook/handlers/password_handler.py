"""Password reset webhook handler."""

import structlog

from app.core.exceptions import PasswordResetError, UserNotFoundError
from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.business.password_service import PasswordService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class PasswordHandler(BaseHandler):
    """Handles the it.password.reset intent.

    Extracts user_id from session parameters, delegates to PasswordService,
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
        """Handle it.password.reset intent fulfillment.

        Args:
            request: Parsed Dialogflow webhook request containing user_id in session params.

        Returns:
            WebhookResponse confirming the reset or surfacing the failure reason.

        Raises:
            MissingParameterError: If user_id is absent from session and intent parameters.
        """
        user_id: str = self._require_param(request, "user_id")
        session_id: str = request.session_info.session

        self.logger.info("password_reset_handling", user_id=user_id, session_id=session_id)

        try:
            result = await self.password_service.initiate_reset(
                user_id=user_id,
                session_id=session_id,
            )
        except UserNotFoundError:
            self.logger.warning("password_handler_user_not_found", user_id=user_id)
            return self.response_builder.build_password_reset_user_not_found(user_id)
        except PasswordResetError as exc:
            self.logger.error("password_handler_reset_error", user_id=user_id, error=str(exc))
            return self.response_builder.build_error_response(str(exc))

        return self.response_builder.build_password_reset_response(result)
