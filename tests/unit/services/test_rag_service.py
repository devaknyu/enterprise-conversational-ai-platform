"""Unit tests for RAGService and LocalEmbeddingBackend. Implemented in Phase 6.

Covers:
- RAGService.retrieve(): top-k, category filtering, error propagation
- LocalEmbeddingBackend.embed(): output shape and dimension
"""

import pytest
import structlog
import chromadb

from app.core.exceptions import EmbeddingError, RAGRetrievalError
from app.services.platform.embedding_backends.base import BaseEmbeddingBackend
from app.services.platform.embedding_backends.local import LocalEmbeddingBackend
from app.services.platform.rag_service import RAGService

_LOGGER = structlog.get_logger("test")
_DIM = 384


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _StubEmbeddingBackend(BaseEmbeddingBackend):
    """Returns a deterministic 384-dim vector for any input text."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * _DIM for _ in texts]


class _FailingEmbeddingBackend(BaseEmbeddingBackend):
    """Always raises EmbeddingError."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingError("embed failed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_collection(
    client: chromadb.EphemeralClient,
    name: str,
    docs: list[str],
    metadatas: list[dict],
) -> chromadb.Collection:
    """Create and populate an ephemeral collection for testing."""
    collection = client.create_collection(name=name)
    vectors = [[0.1] * _DIM for _ in docs]
    ids = [f"chunk_{i}" for i in range(len(docs))]
    collection.add(ids=ids, documents=docs, embeddings=vectors, metadatas=metadatas)
    return collection


def _make_rag_service(
    client: chromadb.EphemeralClient,
    collection_name: str,
    backend: BaseEmbeddingBackend | None = None,
) -> RAGService:
    """Build a RAGService that uses an existing EphemeralClient.

    The persist_dir value is irrelevant here because _client is lazily
    initialized and we immediately replace it with the in-memory client.
    """
    svc = RAGService(
        embedding_backend=backend or _StubEmbeddingBackend(),
        persist_dir=".",  # Unused — overridden below before any retrieve() call.
        collection_name=collection_name,
        logger=_LOGGER,
    )
    svc._client = client
    return svc


# ---------------------------------------------------------------------------
# TestRAGService
# ---------------------------------------------------------------------------

class TestRAGService:
    """Unit tests for RAGService.retrieve()."""

    async def test_retrieve_returns_top_k_chunks(self):
        """retrieve() returns at most top_k chunks ordered by relevance."""
        client = chromadb.EphemeralClient()
        docs = [f"chunk text {i}" for i in range(10)]
        metadatas = [{"category": "vpn-guide", "document_id": f"doc_{i}"} for i in range(10)]
        _seed_collection(client, "test_col", docs, metadatas)

        svc = _make_rag_service(client, "test_col")
        result = await svc.retrieve("some query", top_k=3)

        assert len(result) <= 3

    async def test_retrieve_with_category_filter_restricts_results(self):
        """category_filter restricts retrieval to matching document category."""
        client = chromadb.EphemeralClient()
        docs_a = ["password policy chunk 1", "password policy chunk 2"]
        docs_b = ["vpn guide chunk 1", "vpn guide chunk 2", "vpn guide chunk 3"]
        metadatas_a = [{"category": "password-policy", "document_id": "IT-SEC-001"} for _ in docs_a]
        metadatas_b = [{"category": "vpn-guide", "document_id": "IT-NET-003"} for _ in docs_b]
        _seed_collection(client, "filter_col", docs_a + docs_b, metadatas_a + metadatas_b)

        svc = _make_rag_service(client, "filter_col")
        result = await svc.retrieve("how to reset password", top_k=5, category_filter="password-policy")

        assert len(result) > 0
        # All returned docs must be from the password-policy set.
        for chunk in result:
            assert chunk in docs_a

    async def test_retrieve_raises_on_embedding_failure(self):
        """Embedding backend failure raises EmbeddingError, not a raw exception."""
        client = chromadb.EphemeralClient()
        _seed_collection(client, "err_col", ["some text"], [{"category": "test", "document_id": "X"}])

        svc = _make_rag_service(client, "err_col", backend=_FailingEmbeddingBackend())

        with pytest.raises(EmbeddingError, match="embed failed"):
            await svc.retrieve("query")

    async def test_retrieve_raises_on_chroma_failure(self):
        """ChromaDB query failure raises RAGRetrievalError."""
        client = chromadb.EphemeralClient()
        # Do NOT seed any collection — get_collection will fail.
        svc = _make_rag_service(client, "nonexistent_collection")

        with pytest.raises(RAGRetrievalError):
            await svc.retrieve("query")


# ---------------------------------------------------------------------------
# TestLocalEmbeddingBackend
# ---------------------------------------------------------------------------

class TestLocalEmbeddingBackend:
    """Unit tests for LocalEmbeddingBackend (dev/free path).

    These tests load the real sentence-transformers model — sentence-transformers
    is installed in requirements-dev.txt and the model is cached after first load.
    """

    async def test_embed_returns_vectors_of_correct_dimension(self):
        """embed() returns 384-dim vectors for all-MiniLM-L6-v2."""
        backend = LocalEmbeddingBackend(model_name="all-MiniLM-L6-v2", logger=_LOGGER)
        result = await backend.embed(["How do I reset my password?"])

        assert len(result) == 1
        assert len(result[0]) == 384

    async def test_embed_returns_one_vector_per_input_text(self):
        """embed() returns exactly len(texts) vectors."""
        backend = LocalEmbeddingBackend(model_name="all-MiniLM-L6-v2", logger=_LOGGER)
        texts = ["question one", "question two", "question three"]
        result = await backend.embed(texts)

        assert len(result) == len(texts)
