"""
rag/retriever.py — Embed query and retrieve top-K context chunks from Qdrant.

Performance optimisation:
- embed_single() is CPU-bound (runs the MiniLM model synchronously).
  Wrapping it in run_in_executor() prevents it from blocking the async event
  loop while Qdrant I/O is in flight.
"""

import asyncio
import logging
from functools import partial

from config import get_settings
from vectorstore.embedder import embed_single
from vectorstore.qdrant_client import search

logger = logging.getLogger(__name__)
settings = get_settings()


async def retrieve(
    query: str,
    collection: str | None = None,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[str]:
    """
    Embed the query and return the top-K most relevant text chunks.

    Args:
        query:            The user's question.
        collection:       Qdrant collection name (defaults to config value).
        top_k:            Number of results to return.
        score_threshold:  Minimum cosine similarity to include a result.

    Returns:
        List of text strings, sorted by relevance (highest first).
    """
    col = collection or settings.QDRANT_COLLECTION

    # Offload CPU-bound embedding to a thread-pool so the event loop stays free
    loop = asyncio.get_event_loop()
    query_vector = await loop.run_in_executor(None, partial(embed_single, query))

    results = await search(
        collection=col,
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    chunks = [r["text"] for r in results if r.get("text")]
    logger.debug("Retrieved %d chunks for query: %.60s...", len(chunks), query)
    return chunks
