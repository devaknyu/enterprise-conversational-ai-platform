"""RAG policy question webhook handler. Implemented in Phase 6."""

import structlog

from app.models.dialogflow import WebhookRequest, WebhookResponse
from app.services.platform.llm_service import LLMService
from app.services.platform.rag_service import RAGService
from app.webhook.handlers.base_handler import BaseHandler
from app.webhook.response_builder import ResponseBuilder


class RAGHandler(BaseHandler):
    """Handles the it.policy.query intent using RAG + Gemini.

    Always calls RAGService.retrieve() before LLMService.generate().
    This is enforced here — LLMService never retrieves context itself.
    """

    def __init__(
        self,
        rag_service: RAGService,
        llm_service: LLMService,
        response_builder: ResponseBuilder,
        logger: structlog.BoundLogger,
    ) -> None:
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.response_builder = response_builder
        self.logger = logger.bind(handler="RAGHandler")

    async def handle(self, request: WebhookRequest) -> WebhookResponse:
        """Handle policy query: retrieve context, then generate grounded response."""
        ...
