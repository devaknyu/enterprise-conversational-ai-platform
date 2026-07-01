"""Intent dispatcher — routes Dialogflow intents to registered handlers.

Implemented in Phase 3a. The dispatcher is the single routing point:
intent display name → handler. Adding a new intent means registering
one new handler here — no changes to the route or middleware.
"""

import structlog

from app.core.exceptions import IntentNotFoundError
from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.webhook.handlers.base_handler import BaseHandler


class IntentDispatcher:
    """Maps Dialogflow intent display names to registered handlers.

    Handlers are registered at startup via register(). On each webhook
    call, dispatch() looks up the handler by intent name and delegates.
    Raises IntentNotFoundError if no handler is registered for the intent.
    """

    def __init__(self, logger: structlog.BoundLogger) -> None:
        self._handlers: dict[str, BaseHandler] = {}
        self.logger = logger.bind(component="IntentDispatcher")

    def register(self, intent_name: str, handler: BaseHandler) -> None:
        """Register a handler for the given intent display name.

        Args:
            intent_name: Dialogflow intent display name (e.g. "it.password.reset").
            handler: Handler instance that implements BaseHandler.handle().
        """
        self._handlers[intent_name] = handler
        self.logger.info("handler_registered", intent=intent_name)

    async def dispatch(self, request: WebhookRequest) -> WebhookResponse:
        """Route the incoming request to the appropriate handler.

        Args:
            request: Parsed Dialogflow webhook request.

        Returns:
            WebhookResponse from the matched handler.

        Raises:
            IntentNotFoundError: If no handler is registered for the intent.
        """
        intent = request.intent_info.display_name
        handler = self._handlers.get(intent)
        if handler is None:
            raise IntentNotFoundError(f"No handler registered for intent: {intent!r}")
        self.logger.info("dispatching_intent", intent=intent)
        return await handler.handle(request)
