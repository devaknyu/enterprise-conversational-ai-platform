"""Abstract base class for all webhook intent handlers."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.exceptions import MissingParameterError
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

    def _require_param(self, request: WebhookRequest, name: str) -> Any:
        """Extract a required parameter from session or intent parameters.

        Checks session_info.parameters first (accumulated across turns), then
        falls back to intent_info.parameters (current turn only).

        Args:
            request: The incoming webhook request.
            name: Parameter name as configured in Dialogflow CX.

        Returns:
            The parameter value.

        Raises:
            MissingParameterError: If the parameter is absent in both locations.
        """
        val = request.session_info.parameters.get(name)
        if val is None:
            val = request.intent_info.parameters.get(name)
        if val is None:
            raise MissingParameterError(f"Required parameter '{name}' is missing from request")
        return val

    def _get_param(self, request: WebhookRequest, name: str, default: Any = None) -> Any:
        """Extract an optional parameter from session or intent parameters.

        Args:
            request: The incoming webhook request.
            name: Parameter name as configured in Dialogflow CX.
            default: Value to return if the parameter is absent.

        Returns:
            The parameter value, or default if absent.
        """
        val = request.session_info.parameters.get(name)
        if val is None:
            val = request.intent_info.parameters.get(name)
        return val if val is not None else default
