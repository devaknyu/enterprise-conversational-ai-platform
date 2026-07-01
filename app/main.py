"""FastAPI application factory. Implemented in Phase 3a.

The app is created via create_app() — never instantiated at module level
directly. This pattern enables test isolation via dependency_overrides
and allows multiple test clients with different configurations.
"""

import structlog
from fastapi import FastAPI

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Registers middleware (auth, logging), mounts all routers,
    and configures structlog. Called once at startup.

    Returns:
        Configured FastAPI application instance.
    """
    ...


app = create_app()
