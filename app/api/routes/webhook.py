"""Dialogflow CX fulfillment webhook route. Implemented in Phase 3a.

This is the single entry point for all Dialogflow fulfillment calls.
The route function contains zero business logic — it parses the request,
delegates to IntentDispatcher, and returns the response.
"""

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.exceptions import AppBaseError, IntentNotFoundError
from app.dependencies import get_intent_dispatcher
from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.webhook.dispatcher import IntentDispatcher

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    webhook_request: WebhookRequest,
    dispatcher: IntentDispatcher = Depends(get_intent_dispatcher),
) -> WebhookResponse:
    """Main Dialogflow CX webhook fulfillment endpoint.

    Receives intent fulfillment requests from Dialogflow CX,
    routes to the appropriate handler, and returns a fulfillment response.
    JWT authentication is enforced by WebhookAuthMiddleware (not here).

    Always returns HTTP 200 — Dialogflow requires a 200 even for error
    responses. Failure conditions are surfaced in the fulfillment message body.

    Args:
        request: Raw FastAPI request (for request_id from middleware state).
        webhook_request: Parsed and validated Dialogflow webhook payload.
        dispatcher: Injected IntentDispatcher with registered handlers.

    Returns:
        WebhookResponse with fulfillment message for the employee.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "webhook_received",
        intent=webhook_request.intent_info.display_name,
        session=webhook_request.session_info.session,
        request_id=request_id,
    )
    try:
        return await dispatcher.dispatch(webhook_request)
    except IntentNotFoundError:
        logger.warning(
            "intent_not_found",
            intent=webhook_request.intent_info.display_name,
            request_id=request_id,
        )
        return WebhookResponse.fallback(
            "I'm not sure how to help with that. Please try rephrasing or contact IT support."
        )
    except AppBaseError as e:
        logger.error("service_error", error=str(e), request_id=request_id)
        return WebhookResponse.error(
            "I encountered an error processing your request. Please try again."
        )
