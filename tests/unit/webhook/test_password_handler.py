"""Unit tests for PasswordHandler."""

from datetime import datetime, timezone

import pytest

from app.core.exceptions import MissingParameterError, PasswordResetError, UserNotFoundError
from app.models.dialogflow import SessionInfo, WebhookRequest
from app.models.user import PasswordResetResult
from app.webhook.handlers.password_handler import PasswordHandler
from app.webhook.response_builder import ResponseBuilder


def _make_request(user_id: str | None = "john.doe@acme.com", session_id: str = "sess-001") -> WebhookRequest:
    params = {"user_id": user_id} if user_id is not None else {}
    return WebhookRequest(session_info=SessionInfo(session=session_id, parameters=params))


def _reset_result() -> PasswordResetResult:
    return PasswordResetResult(
        success=True,
        user_id="john.doe@acme.com",
        delivery_method="email",
        estimated_delivery_minutes=5,
        ticket_reference="INC0001001",
        reset_at=datetime.now(tz=timezone.utc),
    )


class _MockPasswordService:
    def __init__(self, result: PasswordResetResult | None = None, raises: Exception | None = None):
        self._result = result
        self._raises = raises

    async def initiate_reset(self, user_id: str, session_id: str) -> PasswordResetResult:
        """Return fixture result or raise configured exception."""
        if self._raises:
            raise self._raises
        return self._result  # type: ignore[return-value]


class TestPasswordHandler:
    """Unit tests for PasswordHandler.handle()."""

    async def test_handle_happy_path_returns_confirmation(self, test_logger):
        """Successful password reset returns a message with ticket reference."""
        handler = PasswordHandler(
            password_service=_MockPasswordService(result=_reset_result()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request())
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "INC0001001" in text
        assert "email" in text

    async def test_handle_user_not_found_returns_not_found_message(self, test_logger):
        """UserNotFoundError is caught and returns a user-friendly not-found message."""
        handler = PasswordHandler(
            password_service=_MockPasswordService(raises=UserNotFoundError("not found")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request())
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "john.doe@acme.com" in text

    async def test_handle_password_reset_error_returns_error_message(self, test_logger):
        """PasswordResetError is caught and surfaces the error message."""
        handler = PasswordHandler(
            password_service=_MockPasswordService(raises=PasswordResetError("AD unavailable")),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        response = await handler.handle(_make_request())
        text = response.fulfillment_response.messages[0].text.text[0]
        assert "AD unavailable" in text

    async def test_handle_missing_user_id_raises_missing_parameter_error(self, test_logger):
        """MissingParameterError is raised when user_id is absent from request."""
        handler = PasswordHandler(
            password_service=_MockPasswordService(result=_reset_result()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        with pytest.raises(MissingParameterError):
            await handler.handle(_make_request(user_id=None))

    async def test_handle_reads_user_id_from_session_parameters(self, test_logger):
        """user_id is read from session_info.parameters (accumulated across turns)."""
        handler = PasswordHandler(
            password_service=_MockPasswordService(result=_reset_result()),
            response_builder=ResponseBuilder(),
            logger=test_logger,
        )
        request = WebhookRequest(
            session_info=SessionInfo(
                session="sess-002",
                parameters={"user_id": "jane.smith@acme.com"},
            )
        )
        response = await handler.handle(request)
        assert response.fulfillment_response.messages[0].text.text[0]
