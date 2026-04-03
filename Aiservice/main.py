"""
main.py — FastAPI application entry point.
LIFESPAN: Initializes Redis, Qdrant, Embedding Model, and LLM.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from cache.redis_client import close_redis, init_redis
from config import get_settings
from rag.llm_client import load_llm
from routers import health, query, upload
from ingestion.web_scraper import close_http_client
from vectorstore.embedder import load_embedder
from vectorstore.qdrant_client import close_qdrant, init_qdrant


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise core dependencies on startup; clean up on shutdown."""
    logger.info("Starting up %s (v%s)…", settings.APP_NAME, settings.APP_VERSION)

    # 1. Start Redis connection pool
    await init_redis()

    # 2. Start Qdrant client
    await init_qdrant()

    # 3. Load ML models into RAM (may take ~1-2 mins on first start)
    load_embedder()
    load_llm()

    logger.info("Startup sequence complete. Ready for requests.")
    yield

    # 4. Clean up
    await close_http_client()
    await close_redis()
    await close_qdrant()
    logger.info("Shutdown complete.")


# ── App Definition ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middlewares ───────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(query.router)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Try to use uvloop for a faster event loop (no-op on Windows)
    try:
        import uvloop
        asyncio_loop = "uvloop"
    except ImportError:
        asyncio_loop = "asyncio"

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        reload=settings.DEBUG,
        loop=asyncio_loop,
        log_level="info" if settings.DEBUG else "warning",
    )
