"""Vertex AI embedding backend using text-embedding-004 (production/paid path).

Uses the same GCP IAM auth as VertexAIBackend. 768-dim embeddings.
Only activated when EMBEDDING_BACKEND=vertex_ai. Implemented in Phase 6.
"""

import asyncio

import structlog

from app.core.exceptions import EmbeddingError
from app.services.platform.embedding_backends.base import BaseEmbeddingBackend


class VertexAIEmbeddingBackend(BaseEmbeddingBackend):
    """Embedding backend using Vertex AI text-embedding-004.

    Production backend. Enterprise data residency: embeddings generated
    within GCP boundary. Requires IAM service account with Vertex AI user role.
    """

    def __init__(
        self,
        project: str,
        region: str,
        logger: structlog.BoundLogger,
    ) -> None:
        self.project = project
        self.region = region
        self.logger = logger.bind(embedding_backend="vertex_ai")
        import vertexai
        vertexai.init(project=project, location=region)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Vertex AI text-embedding-004.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of 768-dim float vectors.

        Raises:
            EmbeddingError: If the Vertex AI API call fails.
        """
        try:
            from vertexai.language_models import TextEmbeddingModel
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: model.get_embeddings(texts))
            vectors = [r.values for r in results]
            self.logger.info("embedding_complete", text_count=len(texts))
            return vectors
        except Exception as exc:
            self.logger.error("embedding_failed", error=str(exc))
            raise EmbeddingError(str(exc)) from exc
