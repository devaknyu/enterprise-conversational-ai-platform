"""Internal admin endpoints. Implemented in Phase 3a.

Not exposed publicly — secured behind separate auth in production.
Used for operational tasks like checking ChromaDB collection stats.
"""

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter()


@router.get("/status")
async def admin_status(settings: Settings = Depends(get_settings)) -> dict:
    """Return operational status: ChromaDB document count, backend config.

    Returns:
        Dict with collection stats and current backend configuration.
        Sensitive values (API keys, credentials) are never included.
    """
    return {
        "app_env": settings.app_env,
        "llm_backend": settings.llm_backend,
        "embedding_backend": settings.embedding_backend,
        "use_mock_integrations": settings.use_mock_integrations,
        "chroma_collection": settings.chroma_collection_name,
    }
