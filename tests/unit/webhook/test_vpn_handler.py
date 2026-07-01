"""Unit tests for VPNHandler."""

import pytest

from app.core.exceptions import IntegrationError, MissingParameterError, VPNServiceError
from app.models.dialogflow import SessionInfo, WebhookRequest
from app.webhook.handlers.vpn_handler import VPNHandler
from app.webhook.response_builder import ResponseBuilder


def _make_request(**params) -> WebhookRequest:
    return WebhookRequest(session_info=SessionInfo(session="sess-001", parameters=params))


class _MockVPNService:
    def __init__(self, result: dict | None = None, raises: Exception | None = None):
        self._result = result
        self._raises = raises

    async def diagnose(self, user_id: str, session_id: str, symptoms: list[str]) -> dict:
        """Return fixture result or raise configured exception."""
        if self._raises:
            raise self._raises
        return self._result  # type: ignore[return-value]


class TestVPNHandler:
    """Unit tests for VPNHandler.handle()."""

    async def test_handle_no_escalation_returns_diagnosis_and_steps(self, test_logger):
        """Non-escalation diagnosis returns steps embedded in the response text."""
        handler = VPNHandler(
            vpn_service=_MockVPNService(result={
                "diagnosis": "VPN tunnel failure detected.",
                "steps": ["Restart VPN client", "Re-enter credentials"],
                "escalate": False,
            }),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "VPN tunnel failure" in text
        assert "Restart VPN client" in text
        assert "Re-enter credentials" in text

    async def test_handle_escalation_path_includes_escalation_advisory(self, test_logger):
        """Escalation flag in result adds an advisory to contact an IT specialist."""
        handler = VPNHandler(
            vpn_service=_MockVPNService(result={
                "diagnosis": "Critical VPN infrastructure failure.",
                "steps": ["Contact networking team"],
                "escalate": True,
            }),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "specialist" in text.lower() or "escalat" in text.lower()

    async def test_handle_vpn_service_error_returns_error_response(self, test_logger):
        """VPNServiceError is caught and returns an unavailability message."""
        handler = VPNHandler(
            vpn_service=_MockVPNService(raises=VPNServiceError("Gateway unreachable")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert len(text) > 0

    async def test_handle_integration_error_returns_error_response(self, test_logger):
        """IntegrationError (propagated from VPNService) is also caught gracefully."""
        handler = VPNHandler(
            vpn_service=_MockVPNService(raises=IntegrationError("VPN gateway timeout")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert len(text) > 0

    async def test_handle_missing_user_id_raises_missing_parameter_error(self, test_logger):
        """MissingParameterError raised when user_id is absent from request."""
        handler = VPNHandler(
            vpn_service=_MockVPNService(result={"diagnosis": "", "steps": [], "escalate": False}),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        with pytest.raises(MissingParameterError):
            await handler.handle(_make_request())

    async def test_handle_uses_empty_list_when_symptoms_absent(self, test_logger):
        """Handler passes an empty symptoms list when the parameter is not provided."""
        received_symptoms: list[list[str]] = []

        class _CapturingVPNService:
            async def diagnose(self, user_id: str, session_id: str, symptoms: list[str]) -> dict:
                """Capture symptoms for assertion."""
                received_symptoms.append(symptoms)
                return {"diagnosis": "No issues.", "steps": [], "escalate": False}

        handler = VPNHandler(
            vpn_service=_CapturingVPNService(),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        await handler.handle(_make_request(user_id="john.doe@acme.com"))
        assert received_symptoms[0] == []
