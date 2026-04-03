"""
routers/health.py — Liveness and Readiness checks.
"""

from fastapi import APIRouter, Response, status
from cache.redis_client import get_redis
from vectorstore.qdrant_client import get_qdrant

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(response: Response):
    """
    Readiness check: verifies connectivity to Qdrant and Redis.
    Returns 503 if any dependency is down.
    """
    details = {
        "qdrant": "disconnected",
        "redis": "disconnected",
    }
    is_ready = True

    # Check Redis
    try:
        redis = get_redis()
        await redis.ping()
        details["redis"] = "connected"
    except Exception:
        is_ready = False

    # Check Qdrant
    try:
        qdrant = get_qdrant()
        await qdrant.get_collections()
        details["qdrant"] = "connected"
    except Exception:
        is_ready = False

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not ready",
        "dependencies": details
    }
