"""Vertex AI backend using the vertexai SDK (production/paid path).

Uses IAM authentication — no API key needed on Cloud Run (service account
attached at deploy time). Model: gemini-1.5-pro.

Only activated when LLM_BACKEND=vertex_ai. See adr/003-gemini-vertex-sdk.md.
"""

import structlog
import vertexai
from google.api_core import exceptions as google_exceptions
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from vertexai.generative_models import GenerativeModel

from app.core.exceptions import LLMError
from app.services.platform.llm_backends.base import BaseLLMBackend


class VertexAIBackend(BaseLLMBackend):
    """LLM backend using the vertexai SDK with GCP IAM auth.

    Production backend. Enterprise features: data residency within GCP,
    IAM-based access control, Cloud Audit Logs for every inference call.
    See adr/003-gemini-vertex-sdk.md.
    """

    def __init__(
        self,
        project: str,
        region: str,
        model: str,
        logger: structlog.BoundLogger,
        max_retries: int = 3,
    ) -> None:
        self.project = project
        self.region = region
        self.model = model
        self.max_retries = max_retries
        self.logger = logger.bind(llm_backend="vertex_ai", model=model)
        vertexai.init(project=project, location=region)

    async def generate(self, prompt: str) -> str:
        """Generate a response using Gemini 1.5 Pro via Vertex AI.

        Args:
            prompt: Complete prompt string assembled by LLMService.

        Returns:
            Generated text from gemini-1.5-pro.

        Raises:
            LLMError: If the Vertex AI API call fails after retries or returns no content.
        """
        self.logger.info("llm_generate_start", prompt_length=len(prompt))
        vertex_model = GenerativeModel(self.model)
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
                    response = await vertex_model.generate_content_async(prompt)
        except google_exceptions.GoogleAPIError as exc:
            self.logger.error("llm_generate_failed", error=str(exc), attempts=attempt_count)
            raise LLMError(str(exc)) from exc

        if not response.text:
            raise LLMError("Vertex AI returned empty response")

        self.logger.info(
            "llm_generate_complete",
            response_length=len(response.text),
            attempts=attempt_count,
        )
        return response.text
