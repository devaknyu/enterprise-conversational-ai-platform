"""Pydantic models for Dialogflow CX webhook request and response payloads.

These models mirror the Dialogflow CX fulfillment webhook format exactly.
FastAPI validates all incoming /webhook POST bodies against WebhookRequest.
All responses are built via ResponseBuilder and serialized as WebhookResponse.

Reference: https://cloud.google.com/dialogflow/cx/docs/reference/rest/v3/WebhookRequest
"""

from typing import Any
from pydantic import BaseModel


class IntentInfo(BaseModel):
    """Intent match information from Dialogflow CX."""

    last_matched_intent: str = ""
    display_name: str = ""
    parameters: dict[str, Any] = {}
    confidence: float = 0.0


class PageInfo(BaseModel):
    """Current page information from Dialogflow CX."""

    current_page: str = ""
    display_name: str = ""


class SessionInfo(BaseModel):
    """Session parameters and session ID from Dialogflow CX."""

    session: str = ""
    parameters: dict[str, Any] = {}


class FulfillmentInfo(BaseModel):
    """Fulfillment tag configured on the Dialogflow CX webhook call."""

    tag: str = ""


class WebhookRequest(BaseModel):
    """Dialogflow CX fulfillment webhook request payload.

    Dialogflow POSTs this to POST /webhook on every fulfillment call.
    FastAPI validates and deserializes it automatically via the route signature.
    """

    detect_intent_response_id: str = ""
    intent_info: IntentInfo = IntentInfo()
    page_info: PageInfo = PageInfo()
    session_info: SessionInfo = SessionInfo()
    fulfillment_info: FulfillmentInfo = FulfillmentInfo()
    text: str = ""

    model_config = {"populate_by_name": True}


class TextMessage(BaseModel):
    """A text message in the Dialogflow CX fulfillment response."""

    text: list[str]


class ResponseMessage(BaseModel):
    """A single message in the fulfillment response."""

    text: TextMessage


class FulfillmentResponse(BaseModel):
    """The fulfillment response body sent back to Dialogflow CX."""

    messages: list[ResponseMessage]
    merge_behavior: str = "REPLACE"


class WebhookResponse(BaseModel):
    """Complete Dialogflow CX webhook response.

    Returned from POST /webhook and serialized to JSON by FastAPI.
    Build this via ResponseBuilder, not by constructing it directly.
    """

    fulfillment_response: FulfillmentResponse

    @classmethod
    def fallback(cls, message: str) -> "WebhookResponse":
        """Build a graceful fallback response when no handler matches.

        Args:
            message: The text to display to the employee.

        Returns:
            A WebhookResponse with the fallback message.
        """
        return cls(
            fulfillment_response=FulfillmentResponse(
                messages=[ResponseMessage(text=TextMessage(text=[message]))]
            )
        )

    @classmethod
    def error(cls, message: str) -> "WebhookResponse":
        """Build an error response for service or auth failures.

        Args:
            message: The error text to display to the employee.

        Returns:
            A WebhookResponse with the error message.
        """
        return cls(
            fulfillment_response=FulfillmentResponse(
                messages=[ResponseMessage(text=TextMessage(text=[message]))]
            )
        )
