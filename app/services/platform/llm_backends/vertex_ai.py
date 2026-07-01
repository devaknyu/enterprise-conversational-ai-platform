"""Vertex AI backend using the vertexai SDK (production/paid path).

Uses IAM authentication — no API key needed on Cloud Run (service account
attached at deploy time). Model: gemini-1.5-pro.

Only activated when LLM_BACKEND=vertex_ai. Implemented in Phase 5.
"""

import structlog

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
    ) -> None:
        self.project = project
        self.region = region
        self.model = model
        self.logger = logger.bind(llm_backend="vertex_ai", model=model)

    async def generate(self, prompt: str) -> str:
        """Generate a response using Gemini 1.5 Pro via Vertex AI.

        Args:
            prompt: Complete prompt string assembled by LLMService.

        Returns:
            Generated text from gemini-1.5-pro.

        Raises:
            LLMError: If the Vertex AI API call fails or returns no content.
        """
        ...
