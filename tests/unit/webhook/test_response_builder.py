"""Unit tests for ResponseBuilder. Implemented in Phase 3a."""

from datetime import datetime, timezone

from app.models.dialogflow import WebhookResponse
from app.models.ticket import IncidentResult
from app.models.user import PasswordResetResult
from app.webhook.response_builder import ResponseBuilder


def _make_password_result() -> PasswordResetResult:
    return PasswordResetResult(
        success=True,
        user_id="john.doe@acme.com",
        delivery_method="email",
        estimated_delivery_minutes=5,
        ticket_reference="AD-RESET-001",
        reset_at=datetime.now(timezone.utc),
    )


def _make_ticket_result() -> IncidentResult:
    return IncidentResult(
        ticket_number="INC0001234",
        short_description="VPN connection failure",
        state="In Progress",
        priority="2 - High",
        assigned_to="IT Team",
        created_at=datetime.now(timezone.utc),
        caller_id="john.doe@acme.com",
    )


def _get_text(response: WebhookResponse) -> str:
    return response.fulfillment_response.messages[0].text.text[0]


class TestResponseBuilder:
    """Unit tests for all ResponseBuilder.build_*() methods."""

    def test_build_password_reset_response_includes_ticket_reference(self):
        """Password reset response message includes the AD-RESET ticket reference."""
        result = _make_password_result()
        response = ResponseBuilder().build_password_reset_response(result)
        assert "AD-RESET-001" in _get_text(response)

    def test_build_ticket_created_response_includes_ticket_number(self):
        """Ticket creation response includes the INC ticket number."""
        result = _make_ticket_result()
        response = ResponseBuilder().build_ticket_created_response(result)
        assert "INC0001234" in _get_text(response)

    def test_build_rag_response_includes_generated_text(self):
        """RAG response wraps the generated text in a WebhookResponse."""
        generated = "VPN must use certificate-based auth per policy v2.3."
        response = ResponseBuilder().build_rag_response(generated)
        assert _get_text(response) == generated

    def test_build_error_response_returns_valid_webhook_response(self):
        """Error responses are valid WebhookResponse objects Dialogflow can parse."""
        response = ResponseBuilder().build_error_response("Something went wrong.")
        assert isinstance(response, WebhookResponse)
        assert len(response.fulfillment_response.messages) > 0

    def test_text_response_static_helper_builds_correct_structure(self):
        """_text_response() produces a correctly nested fulfillmentResponse structure."""
        response = ResponseBuilder._text_response("hello world")
        assert response.fulfillment_response.messages[0].text.text[0] == "hello world"
