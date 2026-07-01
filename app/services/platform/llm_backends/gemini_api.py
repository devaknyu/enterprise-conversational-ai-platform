"""Gemini API backend using google-generativeai (dev/free path).

Uses the AI Studio API key (free tier, no billing account required).
Model: gemini-2.0-flash — free limits: 15 RPM, 1500 req/day, 1M tokens/day.

Swap to VertexAIBackend in production by setting LLM_BACKEND=vertex_ai.
Implemented in Phase 5.
"""

import structlog

from app.services.platform.llm_backends.base import BaseLLMBackend


class GeminiAPIBackend(BaseLLMBackend):
    """LLM backend using google-generativeai package with AI Studio API key.

    This is the default development backend — free, no GCP project needed.
    In production, VertexAIBackend replaces this with zero code changes.
    """

    def __init__(self, api_key: str, model: str, logger: structlog.BoundLogger) -> None:
        self.api_key = api_key
        self.model = model
        self.logger = logger.bind(llm_backend="gemini_api", model=model)

    async def generate(self, prompt: str) -> str:
        """Generate a response using Gemini via the AI Studio API.

        Args:
            prompt: Complete prompt string assembled by LLMService.

        Returns:
            Generated text from gemini-2.0-flash (or configured model).

        Raises:
            LLMError: If the API call fails or returns no content.
        """
        ...
