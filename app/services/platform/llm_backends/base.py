"""Abstract base class for LLM backends.

LLMService depends only on this interface. The DI container injects
the correct concrete backend based on LLM_BACKEND env var:
  - gemini_api  → GeminiAPIBackend  (dev/free, google-generativeai)
  - vertex_ai   → VertexAIBackend   (prod/paid, vertexai SDK)

See adr/003-gemini-vertex-sdk.md for the full rationale.
"""

from abc import ABC, abstractmethod


class BaseLLMBackend(ABC):
    """Abstract interface that all LLM backends must implement.

    LLMService calls only generate() — it never imports from
    google-generativeai or vertexai directly.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt.

        Args:
            prompt: The complete prompt string (system instructions +
                RAG context + user query, assembled by LLMService).

        Returns:
            Generated text response from the model.

        Raises:
            LLMError: If the API call fails or returns an empty response.
        """
        ...
