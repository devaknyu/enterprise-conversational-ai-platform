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
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.integrations.active_directory.client import ActiveDirectoryClient
from app.integrations.active_directory.mock import MockActiveDirectoryClient
from app.integrations.servicenow.base import BaseServiceNowClient
from app.integrations.servicenow.client import ServiceNowClient
from app.integrations.servicenow.mock import MockServiceNowClient
from app.integrations.vpn.base import BaseVPNClient
from app.integrations.vpn.client import VPNClient
from app.integrations.vpn.mock import MockVPNClient
from app.services.platform.embedding_backends.base import BaseEmbeddingBackend
from app.services.platform.embedding_backends.local import LocalEmbeddingBackend
from app.services.platform.embedding_backends.vertex_ai import VertexAIEmbeddingBackend
from app.services.platform.llm_backends.base import BaseLLMBackend
from app.services.platform.llm_backends.gemini_api import GeminiAPIBackend
from app.services.platform.llm_backends.vertex_ai import VertexAIBackend
from app.services.business.auth_service import AuthService
from app.services.business.escalation_service import EscalationService
from app.services.business.password_service import PasswordService
from app.services.business.session_service import SessionService
from app.services.business.ticket_service import TicketService
from app.services.business.vpn_service import VPNService
from app.webhook.dispatcher import IntentDispatcher
from app.webhook.handlers.escalation_handler import EscalationHandler
from app.webhook.handlers.password_handler import PasswordHandler
from app.webhook.handlers.ticket_handler import TicketHandler
from app.webhook.handlers.vpn_handler import VPNHandler
from app.webhook.response_builder import ResponseBuilder


def get_logger() -> structlog.BoundLogger:
    """Provide a structlog logger instance."""
    return structlog.get_logger()


def get_llm_backend(
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> BaseLLMBackend:
    """Provide the configured LLM backend based on LLM_BACKEND env var.

    Returns:
        GeminiAPIBackend when LLM_BACKEND=gemini_api (dev/free default).
        VertexAIBackend when LLM_BACKEND=vertex_ai (production).
    """
    if settings.llm_backend == "gemini_api":
        return GeminiAPIBackend(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            logger=logger,
        )
    return VertexAIBackend(
        project=settings.google_cloud_project,
        region=settings.google_cloud_region,
        model=settings.vertex_ai_model,
        logger=logger,
    )


def get_embedding_backend(
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> BaseEmbeddingBackend:
    """Provide the configured embedding backend based on EMBEDDING_BACKEND env var.

    Returns:
        LocalEmbeddingBackend when EMBEDDING_BACKEND=local (dev/free default).
        VertexAIEmbeddingBackend when EMBEDDING_BACKEND=vertex_ai (production).
    """
    if settings.embedding_backend == "local":
        return LocalEmbeddingBackend(
            model_name=settings.embedding_model_local,
            logger=logger,
        )
    return VertexAIEmbeddingBackend(
        project=settings.google_cloud_project,
        region=settings.google_cloud_region,
        logger=logger,
    )


def get_ad_client(
    settings: Settings = Depends(get_settings),
) -> BaseActiveDirectoryClient:
    """Provide the Active Directory client based on USE_MOCK_INTEGRATIONS."""
    if settings.use_mock_integrations:
        return MockActiveDirectoryClient(
            error_rate=settings.mock_error_rate,
            latency_min_ms=settings.mock_latency_ms_min,
            latency_max_ms=settings.mock_latency_ms_max,
        )
    return ActiveDirectoryClient(
        base_url=settings.ad_base_url,
        service_account=settings.ad_service_account,
        logger=structlog.get_logger(),
    )


def get_servicenow_client(
    settings: Settings = Depends(get_settings),
) -> BaseServiceNowClient:
    """Provide the ServiceNow client based on USE_MOCK_INTEGRATIONS."""
    if settings.use_mock_integrations:
        return MockServiceNowClient(
            error_rate=settings.mock_error_rate,
            latency_min_ms=settings.mock_latency_ms_min,
            latency_max_ms=settings.mock_latency_ms_max,
        )
    return ServiceNowClient(
        base_url=settings.servicenow_base_url,
        username=settings.servicenow_username,
        password=settings.servicenow_password,
        logger=structlog.get_logger(),
    )


def get_vpn_client(
    settings: Settings = Depends(get_settings),
) -> BaseVPNClient:
    """Provide the VPN client based on USE_MOCK_INTEGRATIONS."""
    if settings.use_mock_integrations:
        return MockVPNClient(
            error_rate=settings.mock_error_rate,
            latency_min_ms=settings.mock_latency_ms_min,
            latency_max_ms=settings.mock_latency_ms_max,
        )
    return VPNClient(
        base_url=settings.vpn_api_base_url,
        api_key=settings.vpn_api_key,
        logger=structlog.get_logger(),
    )


# ---------------------------------------------------------------------------
# Service providers
# ---------------------------------------------------------------------------

def get_session_service(
    logger: structlog.BoundLogger = Depends(get_logger),
) -> SessionService:
    """Provide an in-memory SessionService. Phase 3b implementation."""
    return SessionService(logger=logger)


def get_auth_service(
    ad_client: BaseActiveDirectoryClient = Depends(get_ad_client),
    session_service: SessionService = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> AuthService:
    """Provide an AuthService for employee identity verification. Phase 3b."""
    return AuthService(ad_client=ad_client, session_service=session_service, logger=logger)


def get_password_service(
    ad_client: BaseActiveDirectoryClient = Depends(get_ad_client),
    session_service: SessionService = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> PasswordService:
    """Provide a PasswordService with injected AD client and session service."""
    return PasswordService(ad_client=ad_client, session_service=session_service, logger=logger)


def get_ticket_service(
    servicenow_client: BaseServiceNowClient = Depends(get_servicenow_client),
    session_service: SessionService = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> TicketService:
    """Provide a TicketService with injected ServiceNow client and session service."""
    return TicketService(
        servicenow_client=servicenow_client, session_service=session_service, logger=logger
    )


def get_vpn_service(
    vpn_client: BaseVPNClient = Depends(get_vpn_client),
    session_service: SessionService = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> VPNService:
    """Provide a VPNService with injected VPN client and session service."""
    return VPNService(vpn_client=vpn_client, session_service=session_service, logger=logger)


def get_escalation_service(
    servicenow_client: BaseServiceNowClient = Depends(get_servicenow_client),
    session_service: SessionService = Depends(get_session_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> EscalationService:
    """Provide an EscalationService with injected ServiceNow client and session service."""
    return EscalationService(
        servicenow_client=servicenow_client, session_service=session_service, logger=logger
    )


def get_intent_dispatcher(
    password_service: PasswordService = Depends(get_password_service),
    ticket_service: TicketService = Depends(get_ticket_service),
    vpn_service: VPNService = Depends(get_vpn_service),
    escalation_service: EscalationService = Depends(get_escalation_service),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> IntentDispatcher:
    """Provide a fully-wired IntentDispatcher with all production handlers registered.

    A single TicketHandler instance is registered under both it.ticket.create and
    it.ticket.status — the handler branches on fulfillment_info.tag internally.
    RAGHandler is registered in Phase 6 once LLMService and RAGService are available.
    """
    builder = ResponseBuilder()
    dispatcher = IntentDispatcher(logger=logger)

    ticket_handler = TicketHandler(
        ticket_service=ticket_service, response_builder=builder, logger=logger
    )

    dispatcher.register(
        "it.password.reset",
        PasswordHandler(password_service=password_service, response_builder=builder, logger=logger),
    )
    dispatcher.register("it.ticket.create", ticket_handler)
    dispatcher.register("it.ticket.status", ticket_handler)
    dispatcher.register(
        "it.vpn.troubleshoot",
        VPNHandler(vpn_service=vpn_service, response_builder=builder, logger=logger),
    )
    dispatcher.register(
        "it.escalate",
        EscalationHandler(escalation_service=escalation_service, response_builder=builder, logger=logger),
    )

    return dispatcher


def get_llm_service(
    backend: BaseLLMBackend = Depends(get_llm_backend),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide an LLMService with injected backend. Implemented in Phase 5."""
    ...


def get_rag_service(
    embedding_backend: BaseEmbeddingBackend = Depends(get_embedding_backend),
    settings: Settings = Depends(get_settings),
    logger: structlog.BoundLogger = Depends(get_logger),
) -> object:
    """Provide a RAGService with injected embedding backend. Implemented in Phase 6."""
    ...
