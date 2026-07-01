"""Vertex AI embedding backend using text-embedding-004 (production/paid path).

Uses the same GCP IAM auth as VertexAIBackend. 768-dim embeddings.
Only activated when EMBEDDING_BACKEND=vertex_ai. Implemented in Phase 6.
"""

import structlog

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

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Vertex AI text-embedding-004.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of 768-dim float vectors.

        Raises:
            EmbeddingError: If the Vertex AI API call fails.
        """
        ...
