"""Abstract base class for all webhook intent handlers."""

from abc import ABC, abstractmethod

from app.models.dialogflow import WebhookRequest, WebhookResponse


class BaseHandler(ABC):
    """Abstract base for all Dialogflow intent handlers.

    Each handler is responsible for exactly one intent (or a closely
    related group). It extracts parameters from the webhook request,
    calls the appropriate business service, and returns a WebhookResponse.

    Handlers know about Dialogflow's data shape and the service interface.
    They know nothing about HTTP, authentication, or ChromaDB.
    """

    @abstractmethod
    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle an incoming Dialogflow fulfillment request.

        Args:
            request: Parsed and validated Dialogflow webhook request.

        Returns:
            WebhookResponse with the fulfillment message for the employee.

        Raises:
            MissingParameterError: If a required session parameter is absent.
        """
        ...
