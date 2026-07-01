"""Local embedding backend using sentence-transformers (dev/free path).

Model: all-MiniLM-L6-v2 — 384-dim embeddings, ~80MB download, CPU-friendly.
Runs entirely in-process: no API calls, no cost, no internet for inference.

First run downloads the model from HuggingFace (~80MB, cached locally).
Implemented in Phase 6.
"""

import structlog

from app.services.platform.embedding_backends.base import BaseEmbeddingBackend


class LocalEmbeddingBackend(BaseEmbeddingBackend):
    """Embedding backend using sentence-transformers running locally.

    Dev/free path. Production swap: set EMBEDDING_BACKEND=vertex_ai.
    384-dim embeddings vs 768-dim for Vertex AI text-embedding-004 — quality
    is indistinguishable for an IT knowledge base at this scale (~2000 chunks).
    """

    def __init__(self, model_name: str, logger: structlog.BoundLogger) -> None:
        self.model_name = model_name
        self.logger = logger.bind(embedding_backend="local", model=model_name)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the local sentence-transformers model.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of 384-dim float vectors.

        Raises:
            EmbeddingError: If the model fails to load or encode.
        """
        ...
