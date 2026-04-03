"""
rag/pipeline.py - Core RAG chain: Cache -> Retrieve -> Prompt -> Generate.

Performance optimisations applied:
- generate() runs in a thread-pool executor so it NEVER blocks the event loop.
- Redis cache writes (response + context) run concurrently via asyncio.gather().
- embed_single() inside retrieve() is also offloaded (see retriever.py).
"""

import asyncio
import logging
import time
from functools import partial

from cache.query_cache import (
    get_cached_context,
    get_cached_response,
    set_cached_context,
    set_cached_response,
)
from config import get_settings
from rag.llm_client import generate
from rag.retriever import retrieve
from security.validators import sanitize_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

# Llama-3 Chat Template tokens
_SYS_OPEN  = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
_USR_OPEN  = "<|start_header_id|>user<|end_header_id|>\n\n"
_AST_OPEN  = "<|start_header_id|>assistant<|end_header_id|>\n\n"
_END       = "<|eot_id|>"

_PROMPT_TEMPLATE = (
    "{sys_open}AI Tutor: Answer using context only. If unsure, say unknown.{end}"
    "{usr_open}Context:\n{{context}}\n\nQuestion: {{query}}{end}"
    "{ast_open}"
).format(
    sys_open=_SYS_OPEN,
    usr_open=_USR_OPEN,
    ast_open=_AST_OPEN,
    end=_END
)


async def run_rag(query: str, collection: str | None = None) -> dict:
    """
    Execute the full RAG pipeline for a query.

    1. Sanitize user input
    2. Check Redis for cached response  (fast path - returns immediately)
    3. If cache miss: retrieve top-K chunks from Qdrant
    4. Format tutor-style prompt
    5. Generate response via LLM in a thread pool (non-blocking)
    6. Write response + context to Redis cache concurrently

    Returns:
        dict with keys: answer, sources, cached, latency_ms
    """
    start_time = time.perf_counter()
    col = collection or settings.QDRANT_COLLECTION

    # 0. Sanitize
    clean_query = sanitize_prompt(query)

    # 1. Check Response Cache (fast path)
    cached_answer = await get_cached_response(clean_query)
    if cached_answer:
        cached_sources = await get_cached_context(clean_query) or []
        latency = (time.perf_counter() - start_time) * 1000
        logger.debug("Cache HIT | latency=%.1fms", latency)
        return {
            "answer": cached_answer,
            "sources": cached_sources,
            "cached": True,
            "latency_ms": round(latency, 2),
        }

    # 2. Retrieve Context Chunks (embed query + Qdrant search)
    chunks = await retrieve(clean_query, collection=col)

    if not chunks:
        latency = (time.perf_counter() - start_time) * 1000
        return {
            "answer": "I'm sorry, I couldn't find any relevant information in my knowledge base to answer that.",
            "sources": [],
            "cached": False,
            "latency_ms": round(latency, 2),
        }

    # 3. Build Prompt
    context_text = "\n\n---\n\n".join(chunks)
    prompt = _PROMPT_TEMPLATE.format(context=context_text, query=clean_query)

    # 4. Generate Answer — run blocking LLM call in a thread pool so the
    #    event loop remains free to serve other requests during inference.
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, partial(generate, prompt))

    # 5. Cache response + context concurrently (fire both at once)
    await asyncio.gather(
        set_cached_response(clean_query, answer),
        set_cached_context(clean_query, chunks),
        return_exceptions=True,   # don't let a Redis hiccup crash the response
    )

    latency = (time.perf_counter() - start_time) * 1000
    logger.info("RAG complete | chunks=%d | latency=%.1fms", len(chunks), latency)
    return {
        "answer": answer,
        "sources": chunks,
        "cached": False,
        "latency_ms": round(latency, 2),
    }
