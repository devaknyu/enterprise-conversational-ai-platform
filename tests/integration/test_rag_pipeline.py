"""Integration tests for the RAG pipeline. Implemented in Phase 6.

Tests the full RAG flow: query embedding → ChromaDB retrieval → LLM generation.
Uses the local embedding backend (sentence-transformers) and an in-memory ChromaDB
collection seeded with real chunks from password-policy.md.
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import chromadb
import pytest
import structlog

from app.core.exceptions import LLMError
from app.models.dialogflow import (
    FulfillmentInfo,
    IntentInfo,
    SessionInfo,
    WebhookRequest,
)
from app.services.platform.embedding_backends.local import LocalEmbeddingBackend
from app.services.platform.llm_backends.base import BaseLLMBackend
from app.services.platform.llm_service import LLMService
from app.services.platform.rag_service import RAGService
from app.webhook.handlers.rag_handler import RAGHandler
from app.webhook.response_builder import ResponseBuilder

_LOGGER = structlog.get_logger("test_integration")

# ---------------------------------------------------------------------------
# Shared fixtures — scope="function" so the embedding model loads only once.
# ---------------------------------------------------------------------------

PASSWORD_POLICY_PATH = (
    Path(__file__).parent.parent.parent / "knowledge_base" / "documents" / "password-policy.md"
)


class _StubLLMBackend(BaseLLMBackend):
    """Returns a fixed string without calling any real LLM."""

    async def generate(self, prompt: str) -> str:
        return "stub answer from LLM"


@pytest.fixture(scope="function")
def embedding_backend() -> LocalEmbeddingBackend:
    """Real sentence-transformers backend shared across all tests in this module."""
    return LocalEmbeddingBackend(model_name="all-MiniLM-L6-v2", logger=_LOGGER)


@pytest.fixture(scope="function")
async def seeded_rag_service(embedding_backend: LocalEmbeddingBackend) -> RAGService:
    """RAGService backed by an in-memory ChromaDB collection seeded with real policy chunks.

    Loads password-policy.md, splits into 5 chunks, embeds with local backend.
    """
    content = PASSWORD_POLICY_PATH.read_text(encoding="utf-8")

    # Simple chunking: split on double-newlines to get natural sections.
    raw_sections = [s.strip() for s in content.split("\n\n") if s.strip()]
    chunks = raw_sections[:8]  # Use up to 8 sections to keep test fast.

    vectors = await embedding_backend.embed(chunks)
    metadatas = [{"category": "password-policy", "document_id": "IT-SEC-001"} for _ in chunks]

    # Unique name per invocation: EphemeralClient shares in-process state across tests.
    collection_name = f"test_kb_{uuid.uuid4().hex[:8]}"
    client = chromadb.EphemeralClient()
    collection = client.create_collection(collection_name)
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=vectors,
        metadatas=metadatas,
    )

    svc = RAGService(
        embedding_backend=embedding_backend,
        persist_dir=".",  # Unused — overridden below before any retrieve() call.
        collection_name=collection_name,
        logger=_LOGGER,
    )
    svc._client = client
    return svc


@pytest.fixture(scope="function")
def llm_service() -> LLMService:
    """LLMService backed by the stub backend — no real Gemini API call."""
    return LLMService(backend=_StubLLMBackend(), logger=_LOGGER)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRAGPipeline:
    """Integration tests for the full RAG retrieve-then-generate pipeline."""

    async def test_retrieval_returns_relevant_chunks(self, seeded_rag_service: RAGService):
        """RAGService.retrieve() returns chunks relevant to a password-related query."""
        chunks = await seeded_rag_service.retrieve("password expiration policy", top_k=3)

        assert len(chunks) > 0
        combined = " ".join(chunks).lower()
        # The password-policy document mentions 90-day expiry — must appear in retrieved chunks.
        assert "90" in combined or "expir" in combined

    async def test_rag_handler_calls_retrieve_before_generate(
        self,
        seeded_rag_service: RAGService,
        llm_service: LLMService,
    ):
        """RAGHandler always calls RAGService.retrieve() before LLMService.generate()."""
        call_order: list[str] = []

        original_retrieve = seeded_rag_service.retrieve
        original_generate = llm_service.generate

        async def spy_retrieve(*args, **kwargs):
            call_order.append("retrieve")
            return await original_retrieve(*args, **kwargs)

        async def spy_generate(*args, **kwargs):
            call_order.append("generate")
            return await original_generate(*args, **kwargs)

        seeded_rag_service.retrieve = spy_retrieve
        llm_service.generate = spy_generate

        try:
            handler = RAGHandler(
                rag_service=seeded_rag_service,
                llm_service=llm_service,
                response_builder=ResponseBuilder(),
                logger=_LOGGER,
            )
            request = WebhookRequest(
                text="What is the password expiration policy?",
                session_info=SessionInfo(session="sess-integration-001"),
                intent_info=IntentInfo(display_name="it.policy.query"),
                fulfillment_info=FulfillmentInfo(tag="policy"),
            )
            await handler.handle(request)
        finally:
            seeded_rag_service.retrieve = original_retrieve
            llm_service.generate = original_generate

        assert call_order == ["retrieve", "generate"]

    async def test_policy_question_returns_grounded_answer(
        self,
        seeded_rag_service: RAGService,
        llm_service: LLMService,
    ):
        """Full RAGHandler.handle() returns a WebhookResponse with generated text."""
        handler = RAGHandler(
            rag_service=seeded_rag_service,
            llm_service=llm_service,
            response_builder=ResponseBuilder(),
            logger=_LOGGER,
        )
        request = WebhookRequest(
            text="How long is the password valid before it expires?",
            session_info=SessionInfo(session="sess-integration-002"),
            intent_info=IntentInfo(display_name="it.policy.query"),
            fulfillment_info=FulfillmentInfo(tag="policy"),
        )

        response = await handler.handle(request)

        messages = response.fulfillment_response.messages
        assert len(messages) == 1
        text_content = messages[0].text.text[0]
        assert "stub answer from LLM" in text_content
