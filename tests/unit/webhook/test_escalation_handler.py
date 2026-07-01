"""Unit tests for EscalationHandler."""

import pytest

from app.core.exceptions import EscalationError, MissingParameterError
from app.models.dialogflow import SessionInfo, WebhookRequest
from app.webhook.handlers.escalation_handler import EscalationHandler
from app.webhook.response_builder import ResponseBuilder


def _make_request(**params) -> WebhookRequest:
    return WebhookRequest(session_info=SessionInfo(session="sess-001", parameters=params))


def _escalation_result(**kwargs) -> dict:
    defaults = {
        "queue_position": 2,
        "estimated_wait_minutes": 10,
        "escalation_ticket": "INC0002000",
    }
    defaults.update(kwargs)
    return defaults


class _MockEscalationService:
    def __init__(self, result: dict | None = None, raises: Exception | None = None):
        self._result = result
        self._raises = raises

    async def escalate(self, user_id: str, session_id: str, reason: str) -> dict:
        """Return fixture result or raise configured exception."""
        if self._raises:
            raise self._raises
        return self._result  # type: ignore[return-value]


class TestEscalationHandler:
    """Unit tests for EscalationHandler.handle()."""

    async def test_handle_happy_path_returns_queue_position_and_wait(self, test_logger):
        """Successful escalation response includes queue position and wait time."""
        handler = EscalationHandler(
            escalation_service=_MockEscalationService(result=_escalation_result()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com", reason="Cannot login"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "2" in text
        assert "10" in text

    async def test_handle_escalation_error_returns_error_response(self, test_logger):
        """EscalationError is caught and returns a fallback message with phone advisory."""
        handler = EscalationHandler(
            escalation_service=_MockEscalationService(raises=EscalationError("Queue unavailable")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request(user_id="john.doe@acme.com"))
        text = response.fulfillment_response.messages[0].text.text[0]
        assert len(text) > 0

    async def test_handle_missing_user_id_raises_missing_parameter_error(self, test_logger):
        """MissingParameterError raised when user_id is absent from request."""
        handler = EscalationHandler(
            escalation_service=_MockEscalationService(result=_escalation_result()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        with pytest.raises(MissingParameterError):
            await handler.handle(_make_request())

    async def test_handle_uses_default_reason_when_reason_absent(self, test_logger):
        """A default escalation reason is used when reason parameter is not in the request."""
        captured: list[str] = []

        class _CapturingService:
            async def escalate(self, user_id: str, session_id: str, reason: str) -> dict:
                """Capture reason for assertion."""
                captured.append(reason)
                return _escalation_result()

        handler = EscalationHandler(
            escalation_service=_CapturingService(),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        await handler.handle(_make_request(user_id="john.doe@acme.com"))
        assert len(captured) == 1
        assert len(captured[0]) > 0
