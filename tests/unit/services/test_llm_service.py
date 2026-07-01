"""Unit tests for LLMService and GeminiAPIBackend.

Covers:
- Prompt assembly with and without RAG context chunks
- Custom vs default system prompt injection
- LLMError propagation from backend failures
- GeminiAPIBackend: successful response extraction
- GeminiAPIBackend: API failure wrapped as LLMError
"""

import pytest
import structlog
from unittest.mock import AsyncMock, MagicMock, patch

from google.api_core import exceptions as google_exceptions

from app.core.exceptions import LLMError
from app.services.platform.llm_backends.base import BaseLLMBackend
from app.services.platform.llm_backends.gemini_api import GeminiAPIBackend
from app.services.platform.llm_service import LLMService

_LOGGER = structlog.get_logger("test")


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _StubBackend(BaseLLMBackend):
    """Stub backend that records the prompt it received."""

    def __init__(self, return_text: str = "stub response") -> None:
        self._return_text = return_text
        self.last_prompt: str = ""

    async def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._return_text


class _FailingBackend(BaseLLMBackend):
    """Stub backend that always raises LLMError."""

    async def generate(self, prompt: str) -> str:
        raise LLMError("backend unavailable")


# ---------------------------------------------------------------------------
# LLMService tests
# ---------------------------------------------------------------------------

class TestLLMService:
    """Unit tests for LLMService.generate()."""

    async def test_generate_calls_backend_with_assembled_prompt(self):
        """generate() passes a prompt containing the query and context chunks to the backend."""
        stub = _StubBackend()
        service = LLMService(backend=stub, logger=_LOGGER)
        query = "How do I connect to VPN?"
        chunk = "Employees can connect to VPN using the GlobalProtect client."

        result = await service.generate(query=query, context_chunks=[chunk])

        assert result == "stub response"
        assert query in stub.last_prompt
        assert chunk in stub.last_prompt
        assert "[Context 1]" in stub.last_prompt

    async def test_generate_without_context_calls_backend_with_query_only(self):
        """generate() with no context_chunks omits the context block in the assembled prompt."""
        stub = _StubBackend()
        service = LLMService(backend=stub, logger=_LOGGER)
        query = "What is the IT helpdesk number?"

        await service.generate(query=query, context_chunks=None)

        assert query in stub.last_prompt
        assert "[Context" not in stub.last_prompt

    async def test_generate_raises_llm_error_on_backend_failure(self):
        """Backend LLMError propagates unchanged through LLMService.generate()."""
        service = LLMService(backend=_FailingBackend(), logger=_LOGGER)

        with pytest.raises(LLMError, match="backend unavailable"):
            await service.generate(query="test query")

    async def test_generate_uses_custom_system_prompt_when_provided(self):
        """A custom system_prompt overrides the default IT assistant prompt."""
        stub = _StubBackend()
        service = LLMService(backend=stub, logger=_LOGGER)
        custom = "You are a custom assistant."

        await service.generate(query="hello", system_prompt=custom)

        assert custom in stub.last_prompt

    async def test_generate_includes_default_system_prompt_when_none_provided(self):
        """The default IT support persona is included when no system_prompt is given."""
        stub = _StubBackend()
        service = LLMService(backend=stub, logger=_LOGGER)

        await service.generate(query="hello")

        assert "IT support assistant" in stub.last_prompt


# ---------------------------------------------------------------------------
# GeminiAPIBackend tests
# ---------------------------------------------------------------------------

class TestGeminiAPIBackend:
    """Unit tests for GeminiAPIBackend (dev/free path)."""

    async def test_generate_returns_text_from_api(self):
        """generate() extracts and returns the text from the Gemini API response object."""
        mock_response = MagicMock()
        mock_response.text = "Here is the IT policy answer"

        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_instance = MagicMock()
            mock_instance.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_cls.return_value = mock_instance

            backend = GeminiAPIBackend(
                api_key="test-key",
                model="gemini-2.0-flash",
                logger=_LOGGER,
                max_retries=1,
            )
            result = await backend.generate("What is the password policy?")

        assert result == "Here is the IT policy answer"
        mock_instance.generate_content_async.assert_awaited_once()

    async def test_generate_raises_llm_error_on_api_failure(self):
        """A GoogleAPIError from the SDK is caught and re-raised as LLMError."""
        api_error = google_exceptions.GoogleAPIError("Service unavailable")

        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_instance = MagicMock()
            mock_instance.generate_content_async = AsyncMock(side_effect=api_error)
            mock_model_cls.return_value = mock_instance

            backend = GeminiAPIBackend(
                api_key="test-key",
                model="gemini-2.0-flash",
                logger=_LOGGER,
                max_retries=1,
            )

            with pytest.raises(LLMError):
                await backend.generate("test prompt")
