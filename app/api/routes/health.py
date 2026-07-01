"""Health and readiness check endpoints. Implemented in Phase 3a.

GET /health — liveness probe (Cloud Run: is the process alive?)
GET /ready  — readiness probe (Cloud Run: is the app ready to serve traffic?)
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness probe endpoint.

    Returns:
        JSON body with status='healthy' and app version.
        Always returns 200 if the process is running.
    """
    return {"status": "healthy", "version": settings.app_version}


@router.get("/ready")
async def ready(settings: Settings = Depends(get_settings)) -> JSONResponse:
    """Readiness probe endpoint.

    Checks that LLM backend credentials are configured. ChromaDB is always
    considered ready in Phase 3a since it initialises lazily on first use.

    Returns:
        JSON body with status='ready' and component statuses.
        HTTP 200 if all checks pass; 503 if any component is not configured.
    """
    checks: dict[str, str] = {}

    if settings.llm_backend == "gemini_api":
        checks["llm"] = "ready" if settings.gemini_api_key else "not_configured"
    else:
        checks["llm"] = "ready" if settings.google_cloud_project else "not_configured"

    checks["chroma"] = "ready"

    all_ready = all(v == "ready" for v in checks.values())
    body = {"status": "ready" if all_ready else "degraded", **checks}
    return JSONResponse(content=body, status_code=200 if all_ready else 503)
