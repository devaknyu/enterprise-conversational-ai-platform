"""Health and readiness check endpoints. Implemented in Phase 3a.

GET /health — liveness probe (Cloud Run: is the process alive?)
GET /ready  — readiness probe (Cloud Run: is the app ready to serve traffic?)
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Liveness probe endpoint.

    Returns:
        JSON body with status='healthy' and app version.
        Always returns 200 if the process is running.
    """
    ...


@router.get("/ready")
async def ready() -> dict:
    """Readiness probe endpoint.

    Checks that ChromaDB collection is accessible and LLM backend
    is configured. Returns 503 if any dependency is not ready.

    Returns:
        JSON body with status='ready' and component statuses.
    """
    ...
