"""Dialogflow CX webhook response builder. Implemented in Phase 3a.

All WebhookResponse construction goes through this class. Handlers never
hand-construct response JSON. This isolates Dialogflow format knowledge
to one place — if the format changes, only this file changes.
"""

from app.models.dialogflow import (
    FulfillmentResponse,
    ResponseMessage,
    TextMessage,
    WebhookResponse,
)
from app.models.ticket import IncidentResult
from app.models.user import PasswordResetResult


class ResponseBuilder:
    """Builds typed WebhookResponse objects from domain model results.

    Every public method corresponds to one intent outcome. Methods are
    named after the outcome, not the intent, so the intent dispatcher
    can use one builder for multiple related responses.
    """

    def build_password_reset_response(self, result: PasswordResetResult) -> WebhookResponse:
        """Build a fulfillment response confirming a successful password reset.

        Args:
            result: The PasswordResetResult from PasswordService.

        Returns:
            WebhookResponse with delivery method and ticket reference in message.
        """
        ...

    def build_password_reset_user_not_found(self, user_id: str) -> WebhookResponse:
        """Build a response for a password reset where the user was not found."""
        ...

    def build_ticket_created_response(self, result: IncidentResult) -> WebhookResponse:
        """Build a response confirming a new IT ticket was created."""
        ...

    def build_ticket_status_response(self, result: IncidentResult) -> WebhookResponse:
        """Build a response with the current status of an existing ticket."""
        ...

    def build_rag_response(self, generated_text: str) -> WebhookResponse:
        """Build a response containing LLM-generated policy answer text."""
        ...

    def build_escalation_response(self, queue_position: int, wait_minutes: int) -> WebhookResponse:
        """Build a response confirming escalation and providing queue information."""
        ...

    def build_error_response(self, message: str) -> WebhookResponse:
        """Build a generic error response for service failures."""
        ...

    @staticmethod
    def _text_response(message: str) -> WebhookResponse:
        """Build a simple single-message WebhookResponse."""
        return WebhookResponse(
            fulfillment_response=FulfillmentResponse(
                messages=[ResponseMessage(text=TextMessage(text=[message]))]
            )
        )
