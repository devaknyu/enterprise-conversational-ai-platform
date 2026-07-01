"""FastAPI dependency providers — the DI wiring layer. Implemented in Phase 3a.

All service instantiation lives here. Routes and handlers declare
dependencies via Depends(get_xyz) — they never call constructors directly.

The LLM and embedding backend selection (free vs paid) is resolved here
based on LLM_BACKEND and EMBEDDING_BACKEND env vars. Zero business logic
changes are needed to swap backends.
"""

import structlog
from fastapi import Depends

from app.config import Settings, get_settings


def get_logger() -> structlog.BoundLogger:
    """Provide a structlog logger instance."""
    return structlog.get_logger()


def get_llm_backend(
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide the configured LLM backend based on LLM_BACKEND env var.

    Returns:
        GeminiAPIBackend when LLM_BACKEND=gemini_api (dev/free default).
        VertexAIBackend when LLM_BACKEND=vertex_ai (production).
    """
    ...


def get_embedding_backend(
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide the configured embedding backend based on EMBEDDING_BACKEND env var.

    Returns:
        LocalEmbeddingBackend when EMBEDDING_BACKEND=local (dev/free default).
        VertexAIEmbeddingBackend when EMBEDDING_BACKEND=vertex_ai (production).
    """
    ...


def get_ad_client(settings: Settings = Depends(get_settings)) -> object:
    """Provide the Active Directory client based on USE_MOCK_INTEGRATIONS."""
    ...


def get_servicenow_client(settings: Settings = Depends(get_settings)) -> object:
    """Provide the ServiceNow client based on USE_MOCK_INTEGRATIONS."""
    ...


def get_vpn_client(settings: Settings = Depends(get_settings)) -> object:
    """Provide the VPN client based on USE_MOCK_INTEGRATIONS."""
    ...


def get_session_service(
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide the SessionService singleton."""
    ...


def get_password_service(
    ad_client: object = Depends(get_ad_client),
    session_service: object = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a PasswordService with injected dependencies."""
    ...


def get_ticket_service(
    servicenow_client: object = Depends(get_servicenow_client),
    session_service: object = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a TicketService with injected dependencies."""
    ...


def get_vpn_service(
    vpn_client: object = Depends(get_vpn_client),
    session_service: object = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a VPNService with injected dependencies."""
    ...


def get_llm_service(
    backend: object = Depends(get_llm_backend),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide an LLMService with injected backend."""
    ...


def get_rag_service(
    embedding_backend: object = Depends(get_embedding_backend),
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a RAGService with injected embedding backend."""
    ...


def get_intent_dispatcher(
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a fully-wired IntentDispatcher with all handlers registered."""
    ...
