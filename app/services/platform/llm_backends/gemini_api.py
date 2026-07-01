"""Gemini API backend using google-generativeai (dev/free path).

Uses the AI Studio API key (free tier, no billing account required).
Model: gemini-2.0-flash — free limits: 15 RPM, 1500 req/day, 1M tokens/day.

Swap to VertexAIBackend in production by setting LLM_BACKEND=vertex_ai.
"""

import google.generativeai as genai
import structlog
from google.api_core import exceptions as google_exceptions
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.exceptions import LLMError
from app.services.platform.llm_backends.base import BaseLLMBackend


class GeminiAPIBackend(BaseLLMBackend):
    """LLM backend using google-generativeai package with AI Studio API key.

    This is the default development backend — free, no GCP project needed.
    In production, VertexAIBackend replaces this with zero code changes.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        logger: structlog.BoundLogger,
        max_retries: int = 3,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.logger = logger.bind(llm_backend="gemini_api", model=model)
        genai.configure(api_key=api_key)

    async def generate(self, prompt: str) -> str:
        """Generate a response using Gemini via the AI Studio API.

        Args:
            prompt: Complete prompt string assembled by LLMService.

        Returns:
            Generated text from gemini-2.0-flash (or configured model).

        Raises:
            LLMError: If the API call fails after retries or returns no content.
        """
        self.logger.info("llm_generate_start", prompt_length=len(prompt))
        genai_model = genai.GenerativeModel(self.model)
        attempt_count = 0

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(initial=1, max=10),
                retry=retry_if_exception_type(google_exceptions.GoogleAPIError),
                reraise=True,
            ):
                with attempt:
                    attempt_count += 1
                    response = await genai_model.generate_content_async(prompt)
        except google_exceptions.GoogleAPIError as exc:
            self.logger.error("llm_generate_failed", error=str(exc), attempts=attempt_count)
            raise LLMError(str(exc)) from exc

        if not response.text:
            raise LLMError("Gemini returned empty response")

        self.logger.info(
            "llm_generate_complete",
            response_length=len(response.text),
            attempts=attempt_count,
        )
        return response.text
