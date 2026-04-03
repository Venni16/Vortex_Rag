"""
config.py — Centralised settings for the RAG AI Tutor Service.
All values can be overridden via environment variables or a .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "RAG AI Tutor Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Security ──────────────────────────────────────────────────────────────
    API_KEY: str = "dev-secret-change-me"
    JWT_SECRET: str = "jwt-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── Rate Limiting (requests per minute) ───────────────────────────────────
    RATE_LIMIT_QUERY: str = "10/minute"
    RATE_LIMIT_UPLOAD: str = "5/minute"

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]

    # ── Embedding Model ───────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384                   # matches all-MiniLM-L6-v2

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_MODEL_NAME: str = "microsoft/Phi-3-mini-4k-instruct"
    LLM_MAX_NEW_TOKENS: int = 512             # slightly higher for Phi-3 depth
    LLM_TEMPERATURE: float = 0.1
    LLM_USE_LLAMA_CPP: bool = True
    LLAMA_CPP_MODEL_PATH: str = "TheBloke/Phi-3-mini-4k-instruct-GGUF"
    LLAMA_CPP_MODEL_FILE: str = "phi-3-mini-4k-instruct.Q4_K_M.gguf"
    # llama-cpp performance knobs (all overridable via .env)
    LLAMA_CPP_N_THREADS: int = 0
    LLAMA_CPP_N_BATCH: int = 512
    LLAMA_CPP_N_CTX: int = 4096

    # ── Vector Store (Qdrant) ─────────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "default"
    RETRIEVAL_TOP_K: int = 3                  # reduced from 5 for 'cleaner' context
    RETRIEVAL_SCORE_THRESHOLD: float = 0.35

    # ── Cache (Redis) ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600              # 1 hour

    # ── Text Chunking ─────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 400                      # words
    CHUNK_OVERLAP: int = 50                    # words

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
