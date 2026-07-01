"""Dialogflow CX fulfillment webhook route. Implemented in Phase 3a.

This is the single entry point for all Dialogflow fulfillment calls.
The route function contains zero business logic — it parses the request,
delegates to IntentDispatcher, and returns the response.
"""

import structlog
from fastapi import APIRouter, Depends, Request

from app.models.dialogflow import WebhookRequest, WebhookResponse

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    webhook_request: WebhookRequest,
) -> WebhookResponse:
    """Main Dialogflow CX webhook fulfillment endpoint.

    Receives intent fulfillment requests from Dialogflow CX,
    routes to the appropriate handler, and returns a fulfillment response.
    JWT authentication is enforced by WebhookAuthMiddleware (not here).

    Args:
        request: Raw FastAPI request (for request_id from middleware state).
        webhook_request: Parsed and validated Dialogflow webhook payload.

    Returns:
        WebhookResponse with fulfillment message for the employee.
    """
    ...
