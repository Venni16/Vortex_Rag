"""
ingestion/background_worker.py — Async background ingestion tasks.
Chunks -> embeds -> upserts into Qdrant, with job-status tracking in Redis.

Performance optimisations:
- chunk_text() is CPU-bound (regex + string ops on large text).
  Wrapped in run_in_executor so it does not block the async event loop.
- embed(chunks) is also CPU-bound (runs the MiniLM SentenceTransformer).
  Wrapped in run_in_executor for the same reason.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from functools import partial

from cache.redis_client import get_redis
from config import get_settings
from ingestion.chunker import chunk_text
from ingestion.deduplicator import generate_chunk_id
from ingestion.refiner import refine_chunk
from vectorstore.embedder import embed
from vectorstore.qdrant_client import get_qdrant
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)
settings = get_settings()

# Status keys stored in Redis: rag:job:<job_id>
_JOB_TTL = 86_400  # 24 hours
# Use a semaphore to ensure only one LLM inference runs at a time on CPU
_LLM_SEMAPHORE = asyncio.Semaphore(1)


def _job_key(job_id: str) -> str:
    return f"rag:job:{job_id}"


async def _set_job_status(job_id: str, status: str, detail: str = "") -> None:
    try:
        redis = get_redis()
        existing = await redis.get(_job_key(job_id))
        data = json.loads(existing) if existing else {"job_id": job_id, "logs": []}

        data["status"] = status
        data["detail"] = detail
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        data["logs"].append(f"[{data['updated_at']}] {status}: {detail}")

        await redis.set(_job_key(job_id), json.dumps(data), ex=_JOB_TTL)
    except Exception as exc:
        logger.warning("Could not update job status: %s", exc)


async def get_job_status(job_id: str) -> dict | None:
    """Retrieve the current status of an ingestion job."""
    try:
        redis = get_redis()
        val = await redis.get(_job_key(job_id))
        return json.loads(val) if val else None
    except Exception:
        return None


async def ingest_document(
    content: str,
    source_id: str,
    collection: str | None = None,
    job_id: str | None = None,
) -> str:
    """
    Background ingestion task:
    1. Chunk text   (CPU-bound — run in executor)
    2. Embed chunks (CPU-bound — run in executor)
    3. Generate deterministic IDs for deduplication
    4. Upsert into Qdrant

    Returns the job_id.
    """
    jid = job_id or str(uuid.uuid4())
    col = collection or settings.QDRANT_COLLECTION
    loop = asyncio.get_event_loop()

    await _set_job_status(jid, "processing", f"Ingesting: {source_id}")
    logger.info("[job:%s] Starting ingestion | source: %s", jid, source_id)

    try:
        # 1. Chunk — CPU-bound, offload to thread pool
        raw_chunks: list[str] = await loop.run_in_executor(
            None, partial(chunk_text, content)
        )
        if not raw_chunks:
            await _set_job_status(jid, "warning", f"No text found in {source_id}")
            return jid

        # 2. Refine & Classify — Use the AI Refiner for each chunk
        refined_metadata = []
        await _set_job_status(jid, "processing", f"Refining {len(raw_chunks)} chunks...")
        
        for i, chunk in enumerate(raw_chunks):
            async with _LLM_SEMAPHORE:
                logger.info("[job:%s] Refining chunk %d/%d", jid, i+1, len(raw_chunks))
                refined = await refine_chunk(chunk)
                refined_metadata.append(refined)

        # 3. Embed — Embed the CLEANED text (higher quality vectors)
        cleaned_chunks = [m.get("cleaned_text", "") for m in refined_metadata]
        await _set_job_status(jid, "processing", "Generating embeddings...")
        vectors: list[list[float]] = await loop.run_in_executor(
            None, partial(embed, cleaned_chunks)
        )

        # 4. Generate deterministic IDs (deduplication via content hash)
        ids = [generate_chunk_id(chunk, source_id) for chunk in raw_chunks]

        # 5. Build PointStructs and upsert
        points = []
        for pid, vec, raw, meta in zip(ids, vectors, raw_chunks, refined_metadata):
            # Payload includes the structured AI metadata + original raw text
            payload = {
                "text": meta.get("cleaned_text", raw),
                "raw_text": raw,
                "source": source_id,
                "framework": meta.get("framework", "other"),
                "topic": meta.get("topic", "general"),
                "subtopic": meta.get("subtopic", "unknown"),
                "keywords": meta.get("keywords", []),
                "difficulty": meta.get("difficulty", "intermediate"),
                "refined": True
            }
            points.append(qmodels.PointStruct(id=pid, vector=vec, payload=payload))

        client = get_qdrant()
        await client.upsert(collection_name=col, points=points)

        logger.info("[job:%s] Upserted %d points for %s.", jid, len(raw_chunks), source_id)
        await _set_job_status(jid, "processing", f"Completed {source_id}")

    except Exception as exc:
        logger.exception("[job:%s] Ingestion failed for %s: %s", jid, source_id, exc)
        await _set_job_status(jid, "failed", f"Error on {source_id}: {exc}")

    return jid
