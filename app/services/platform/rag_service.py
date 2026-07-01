"""RAG retrieval service. Implemented in Phase 6.

Retrieves semantically relevant document chunks from ChromaDB to ground
LLMService responses. Always called before LLMService for policy questions.
"""

import chromadb
import structlog

from app.core.exceptions import EmbeddingError, RAGRetrievalError
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
        # Lazily initialized on first retrieve() call so the app starts without ChromaDB.
        self._client: chromadb.PersistentClient | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        """Return the ChromaDB client, creating it on first access."""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

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
        # EmbeddingError is allowed to propagate — caller handles it separately.
        vectors = await self.embedding_backend.embed([query])
        query_vector = vectors[0]

        try:
            collection = self._get_client().get_collection(name=self.collection_name)
        except Exception as exc:
            raise RAGRetrievalError(
                f"Collection '{self.collection_name}' not found — run scripts/ingest_knowledge_base.py"
            ) from exc

        try:
            query_kwargs: dict = {
                "query_embeddings": [query_vector],
                "n_results": top_k,
            }
            if category_filter is not None:
                query_kwargs["where"] = {"category": category_filter}

            results = collection.query(**query_kwargs)
            chunks: list[str] = results["documents"][0]

            self.logger.info(
                "rag_retrieve",
                query_length=len(query),
                top_k=top_k,
                category_filter=category_filter,
                chunks_returned=len(chunks),
            )
            return chunks
        except EmbeddingError:
            raise
        except Exception as exc:
            self.logger.error("rag_retrieve_failed", error=str(exc))
            raise RAGRetrievalError(str(exc)) from exc
