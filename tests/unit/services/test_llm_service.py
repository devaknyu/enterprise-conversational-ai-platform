"""Unit tests for LLMService. Implemented in Phase 5."""

import pytest


class TestLLMService:
    """Unit tests for LLMService.generate()."""

    async def test_generate_calls_backend_with_assembled_prompt(self):
        """generate() passes a prompt containing query and context chunks to the backend."""
        pass

    async def test_generate_without_context_calls_backend_with_query_only(self):
        """generate() with no context_chunks still calls the backend (no RAG fallback)."""
        pass

    async def test_generate_raises_llm_error_on_backend_failure(self):
        """Backend failure is wrapped in LLMError, not exposed as a raw exception."""
        pass


class TestGeminiAPIBackend:
    """Unit tests for GeminiAPIBackend (dev/free path). Implemented in Phase 5."""

    async def test_generate_returns_text_from_api(self):
        """generate() returns the text from the Gemini API response."""
        pass

    async def test_generate_raises_llm_error_on_api_failure(self):
        """API failure raises LLMError."""
        pass
