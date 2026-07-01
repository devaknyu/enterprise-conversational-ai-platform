"""LLM orchestration service. Implemented in Phase 5.

This is the ONLY file in the codebase that calls any LLM backend.
Handlers and business services never import from google-generativeai or
vertexai — they call LLMService.generate() instead.
"""

import structlog

from app.services.business.base import BaseService
from app.services.platform.llm_backends.base import BaseLLMBackend


class LLMService(BaseService):
    """Orchestrates all LLM inference calls through the configured backend.

    Builds structured prompts (system instructions + RAG context + user query)
    and delegates to the injected BaseLLMBackend. The backend is selected
    at startup by the DI container based on LLM_BACKEND env var.

    Never called for non-RAG intents (password reset, ticket creation, etc.)
    — only for policy questions that require generative responses.
    """

    def __init__(
        self,
        backend: BaseLLMBackend,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.backend = backend

    async def generate(
        self,
        query: str,
        context_chunks: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a response for the given query, optionally with RAG context.

        Always called after RAGService.retrieve() for policy questions.
        context_chunks are prepended to the prompt so the model grounds
        its response in retrieved policy content.

        Args:
            query: The employee's natural language question.
            context_chunks: Retrieved document chunks from RAGService.
                If None or empty, the model answers from its training only.
            system_prompt: Override for the default system instructions.

        Returns:
            Generated response text to send back to Dialogflow.

        Raises:
            LLMError: If the backend call fails after retries.
        """
        ...
