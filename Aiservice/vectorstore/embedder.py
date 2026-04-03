"""
vectorstore/embedder.py — Singleton SentenceTransformer embedding model.
Loaded once at startup — zero per-request overhead.

Performance optimisations:
- batch_size raised from 32 -> 64: MiniLM-L6 handles 64 comfortably and
  cuts iteration count in half for large ingestion batches.
- normalize_embeddings=True: our Qdrant collection uses COSINE distance,
  so normalising at embed time removes internal Qdrant normalisation overhead.
"""

import logging
from typing import Union

from sentence_transformers import SentenceTransformer

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model: SentenceTransformer | None = None

_BATCH_SIZE = 64   # raised from 32 -- MiniLM-L6 handles 64 comfortably


def load_embedder() -> None:
    """Load the embedding model into memory. Call once at application startup."""
    global _model
    logger.info("Loading embedding model: %s ...", settings.EMBEDDING_MODEL)
    _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded (dim=%d).", settings.EMBEDDING_DIM)


def get_embedder() -> SentenceTransformer:
    """Return the loaded embedder. Raises if not initialised."""
    if _model is None:
        raise RuntimeError("Embedder not loaded. Call load_embedder() first.")
    return _model


def embed(texts: Union[str, list[str]]) -> list[list[float]]:
    """
    Embed one or more text strings.

    Args:
        texts: A single string or a list of strings.

    Returns:
        A list of float vectors, one per input text.
    """
    if isinstance(texts, str):
        texts = [texts]
    model = get_embedder()
    vectors = model.encode(
        texts,
        batch_size=_BATCH_SIZE,
        normalize_embeddings=True,   # cosine-ready; removes Qdrant normalisation overhead
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_single(text: str) -> list[float]:
    """Convenience: embed a single string and return its vector."""
    return embed(text)[0]
