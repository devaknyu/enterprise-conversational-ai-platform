"""RAG retrieval service. Implemented in Phase 6.

Retrieves semantically relevant document chunks from ChromaDB to ground
LLMService responses. Always called before LLMService for policy questions.
"""

import structlog

from app.services.business.base import BaseService
from app.services.platform.embedding_backends.base import BaseEmbeddingBackend


class RAGService(BaseService):
    """ChromaDB retrieval service for Retrieval-Augmented Generation.

    Embeds query text using the configured embedding backend, searches
    ChromaDB for the top-k most similar chunks, and returns them for
    inclusion in the LLM prompt.

    The collection must be pre-populated via scripts/ingest_knowledge_base.py
    before any retrieval queries will work.
    """

    def __init__(
        self,
        embedding_backend: BaseEmbeddingBackend,
        persist_dir: str,
        collection_name: str,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.embedding_backend = embedding_backend
        self.persist_dir = persist_dir
        self.collection_name = collection_name

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
    ) -> list[str]:
        """Retrieve the top-k most relevant chunks for the given query.

        Embeds the query, searches ChromaDB using cosine similarity,
        and returns the chunk texts (not the embeddings).

        Args:
            query: The employee's natural language question.
            top_k: Number of chunks to retrieve. Default 5.
            category_filter: Optional metadata filter to restrict search
                to a specific document category (e.g. "password-policy").

        Returns:
            List of chunk text strings, ordered by relevance (most relevant first).

        Raises:
            RAGRetrievalError: If the ChromaDB query fails.
            EmbeddingError: If embedding generation fails.
        """
        ...
