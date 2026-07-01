"""Internal admin endpoints. Implemented in Phase 3a.

Not exposed publicly — secured behind separate auth in production.
Used for operational tasks like checking ChromaDB collection stats.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def admin_status() -> dict:
    """Return operational status: ChromaDB document count, backend config.

    Returns:
        Dict with collection stats and current backend configuration.
    """
    ...
