"""FastAPI application factory. Implemented in Phase 3a.

The app is created via create_app() — never instantiated at module level
directly. This pattern enables test isolation via dependency_overrides
and allows multiple test clients with different configurations.
"""

import structlog
from fastapi import FastAPI

from app.api.middleware.auth import WebhookAuthMiddleware
from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.webhook import router as webhook_router
from app.config import get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Registers middleware (auth, logging), mounts all routers,
    and configures structlog. Called once at startup.

    Middleware execution order (outermost → innermost):
        RequestLoggingMiddleware → WebhookAuthMiddleware → Route
    FastAPI's add_middleware is LIFO, so RequestLoggingMiddleware
    is added last to run outermost (binds request_id before auth fires).

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    configure_logging(settings.log_level, settings.app_env)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url=None,
    )

    app.add_middleware(WebhookAuthMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health_router)
    app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])

    logger.info(
        "app_created",
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )
    return app


app = create_app()
