"""Unit tests for IntentDispatcher. Implemented in Phase 3a."""

import pytest

from app.core.exceptions import IntentNotFoundError
from app.models.dialogflow import IntentInfo, WebhookRequest, WebhookResponse
from app.webhook.dispatcher import IntentDispatcher
from app.webhook.handlers.base_handler import BaseHandler


class _StubHandler(BaseHandler):
    """Minimal handler stub for testing the dispatcher."""

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.call_count = 0

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Record call and return a fixed response."""
        self.call_count += 1
        return WebhookResponse.fallback(self._response_text)


def _make_request(intent: str) -> WebhookRequest:
    return WebhookRequest(intent_info=IntentInfo(display_name=intent))


class TestIntentDispatcher:
    """Unit tests for IntentDispatcher.dispatch() and register()."""

    async def test_dispatch_routes_to_registered_handler(self, test_logger):
        """dispatch() calls the handler registered for the intent name."""
        dispatcher = IntentDispatcher(logger=test_logger)
        handler = _StubHandler("handled")
        dispatcher.register("it.password.reset", handler)

        response = await dispatcher.dispatch(_make_request("it.password.reset"))

        assert handler.call_count == 1
        text = response.fulfillment_response.messages[0].text.text[0]
        assert text == "handled"

    async def test_dispatch_raises_intent_not_found_for_unregistered_intent(self, test_logger):
        """dispatch() raises IntentNotFoundError when no handler is registered."""
        dispatcher = IntentDispatcher(logger=test_logger)

        with pytest.raises(IntentNotFoundError):
            await dispatcher.dispatch(_make_request("it.unknown.intent"))

    def test_register_overwrites_existing_handler(self, test_logger):
        """Registering a second handler for the same intent replaces the first."""
        dispatcher = IntentDispatcher(logger=test_logger)
        handler1 = _StubHandler("first")
        handler2 = _StubHandler("second")

        dispatcher.register("it.password.reset", handler1)
        dispatcher.register("it.password.reset", handler2)

        assert dispatcher._handlers["it.password.reset"] is handler2
