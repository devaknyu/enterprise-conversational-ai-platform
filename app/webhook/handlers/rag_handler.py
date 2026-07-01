"""RAG policy question webhook handler. Implemented in Phase 6."""

import structlog

from app.core.exceptions import EmbeddingError, LLMError, RAGRetrievalError
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
        query: str = request.text or self._get_param(request, "query", default="")
        category: str | None = self._get_param(request, "category")
        session_id: str = request.session_info.session

        self.logger.info(
            "rag_handler_start",
            query_length=len(query),
            session_id=session_id,
            category_filter=category,
        )

        try:
            chunks = await self.rag_service.retrieve(query, category_filter=category)
            generated = await self.llm_service.generate(query, context_chunks=chunks)
        except (EmbeddingError, RAGRetrievalError, LLMError) as exc:
            self.logger.error("rag_handler_error", error=str(exc), session_id=session_id)
            return self.response_builder.build_error_response(
                "I'm having trouble accessing the knowledge base right now. "
                "Please try again or contact the IT helpdesk directly."
            )

        self.logger.info(
            "rag_handler_complete",
            chunks_used=len(chunks),
            response_length=len(generated),
            session_id=session_id,
        )
        return self.response_builder.build_rag_response(generated)
