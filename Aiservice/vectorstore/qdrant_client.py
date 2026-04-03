"""
vectorstore/qdrant_client.py — Async Qdrant wrapper for upsert + search.
"""

import logging
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: AsyncQdrantClient | None = None


async def init_qdrant() -> None:
    """Connect to Qdrant and ensure the default collection exists."""
    global _client
    _client = AsyncQdrantClient(url=settings.QDRANT_URL)
    await ensure_collection(settings.QDRANT_COLLECTION)
    logger.info("Qdrant connected at %s", settings.QDRANT_URL)


async def close_qdrant() -> None:
    """Close the Qdrant connection."""
    global _client
    if _client:
        await _client.close()
        _client = None


def get_qdrant() -> AsyncQdrantClient:
    """Return the active Qdrant client."""
    if _client is None:
        raise RuntimeError("Qdrant client not initialised. Call init_qdrant() first.")
    return _client


async def ensure_collection(name: str, vector_size: int | None = None) -> None:
    """
    Create a Qdrant collection if it doesn't already exist.
    Idempotent — safe to call on every startup.
    """
    size = vector_size or settings.EMBEDDING_DIM
    client = get_qdrant()
    existing = {c.name for c in (await client.get_collections()).collections}
    if name not in existing:
        await client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=size,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection '%s' (dim=%d).", name, size)


async def upsert_chunks(
    collection: str,
    chunks: list[str],
    vectors: list[list[float]],
    metadata: list[dict] | None = None,
) -> None:
    """
    Upsert text chunks with their embedding vectors into a collection.
    Each chunk gets a random UUID as its point ID.
    """
    if not chunks:
        return

    meta = metadata or [{} for _ in chunks]
    points = [
        qmodels.PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"text": chunk, **m},
        )
        for chunk, vec, m in zip(chunks, vectors, meta)
    ]
    client = get_qdrant()
    await client.upsert(collection_name=collection, points=points)
    logger.debug("Upserted %d chunks into collection '%s'.", len(points), collection)


async def search(
    collection: str,
    query_vector: list[float],
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[dict]:
    """
    Perform a vector similarity search. Returns list of dicts with
    keys: text, score, and any extra payload fields.
    """
    k = top_k or settings.RETRIEVAL_TOP_K
    threshold = score_threshold or settings.RETRIEVAL_SCORE_THRESHOLD
    client = get_qdrant()

    results = await client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=k,
        score_threshold=threshold,
        with_payload=True,
    )
    return [
        {"text": r.payload.get("text", ""), "score": r.score, **r.payload}
        for r in results
    ]
