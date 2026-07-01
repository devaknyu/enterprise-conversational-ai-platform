"""Abstract base class for embedding backends.

RAGService depends only on this interface. The DI container injects
the correct concrete backend based on EMBEDDING_BACKEND env var:
  - local      → LocalEmbeddingBackend  (dev/free, sentence-transformers)
  - vertex_ai  → VertexAIEmbeddingBackend  (prod/paid, Vertex AI text-embedding-004)
"""

from abc import ABC, abstractmethod


class BaseEmbeddingBackend(ABC):
    """Abstract interface that all embedding backends must implement.

    RAGService calls only embed() — it never imports sentence-transformers
    or the Vertex AI client directly.
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a list of text strings.

        Args:
            texts: List of text strings to embed. For ingestion, these are
                document chunks. For retrieval, this is a single-element list
                containing the query string.

        Returns:
            List of embedding vectors, one per input text. Each vector is
            a list of floats (384 dims for local backend, 768 for Vertex AI).

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        ...
