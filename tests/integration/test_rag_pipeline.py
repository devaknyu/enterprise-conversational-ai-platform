"""Integration tests for the RAG pipeline. Implemented in Phase 6.

Tests the full RAG flow: query embedding → ChromaDB retrieval → LLM generation.
Uses the local embedding backend (sentence-transformers) and a test ChromaDB collection.
"""

import pytest


class TestRAGPipeline:
    """Integration tests for the full RAG retrieve-then-generate pipeline."""

    async def test_policy_question_returns_grounded_answer(self):
        """A policy question returns a response grounded in the knowledge base."""
        pass

    async def test_retrieval_returns_relevant_chunks(self):
        """RAGService.retrieve() returns chunks relevant to the query."""
        pass

    async def test_rag_handler_calls_retrieve_before_generate(self):
        """RAGHandler always calls RAGService.retrieve() before LLMService.generate()."""
        pass
