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
        msg = (
            f"Your password reset has been sent to your {result.delivery_method}. "
            f"It should arrive within {result.estimated_delivery_minutes} minutes. "
            f"Reference: {result.ticket_reference}."
        )
        return self._text_response(msg)

    def build_password_reset_user_not_found(self, user_id: str) -> WebhookResponse:
        """Build a response for a password reset where the user was not found."""
        return self._text_response(
            f"I couldn't find an account for {user_id!r}. "
            "Please verify your employee ID or contact IT support directly."
        )

    def build_ticket_created_response(self, result: IncidentResult) -> WebhookResponse:
        """Build a response confirming a new IT ticket was created."""
        msg = (
            f"IT ticket {result.ticket_number} has been created: {result.short_description}. "
            f"Priority: {result.priority}. You'll receive email updates as the ticket progresses."
        )
        return self._text_response(msg)

    def build_ticket_status_response(self, result: IncidentResult) -> WebhookResponse:
        """Build a response with the current status of an existing ticket."""
        msg = (
            f"Ticket {result.ticket_number}: {result.state}. "
            f"{result.short_description}. Assigned to: {result.assigned_to}."
        )
        return self._text_response(msg)

    def build_rag_response(self, generated_text: str) -> WebhookResponse:
        """Build a response containing LLM-generated policy answer text."""
        return self._text_response(generated_text)

    def build_escalation_response(self, queue_position: int, wait_minutes: int) -> WebhookResponse:
        """Build a response confirming escalation and providing queue information."""
        msg = (
            f"I've escalated your request to an IT specialist. "
            f"You're #{queue_position} in the queue with an estimated wait of ~{wait_minutes} minutes."
        )
        return self._text_response(msg)

    def build_vpn_response(self, diagnosis: str, steps: list[str]) -> WebhookResponse:
        """Build a VPN troubleshooting response with diagnosis and numbered steps.

        Args:
            diagnosis: One-sentence summary of the VPN issue or status.
            steps: Ordered list of remediation actions for the employee.
        """
        if steps:
            steps_text = " ".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
            msg = f"{diagnosis} {steps_text}"
        else:
            msg = diagnosis
        return self._text_response(msg)

    def build_vpn_escalation_response(self, diagnosis: str, steps: list[str]) -> WebhookResponse:
        """Build a VPN response that includes an advisory to escalate to IT.

        Args:
            diagnosis: One-sentence summary of the VPN issue.
            steps: Ordered list of steps to try before escalating.
        """
        if steps:
            steps_text = " ".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
            msg = (
                f"{diagnosis} {steps_text} "
                "If the issue persists after these steps, I recommend escalating to an IT specialist."
            )
        else:
            msg = (
                f"{diagnosis} "
                "I recommend escalating this to an IT specialist for further investigation."
            )
        return self._text_response(msg)

    def build_error_response(self, message: str) -> WebhookResponse:
        """Build a generic error response for service failures."""
        return self._text_response(message)

    @staticmethod
    def _text_response(message: str) -> WebhookResponse:
        """Build a simple single-message WebhookResponse."""
        return WebhookResponse(
            fulfillment_response=FulfillmentResponse(
                messages=[ResponseMessage(text=TextMessage(text=[message]))]
            )
        )
