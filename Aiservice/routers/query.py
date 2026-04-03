"""
routers/query.py — The main RAG query endpoint.
"""

import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from config import get_settings
from rag.pipeline import run_rag
from security.auth import verify_api_key

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["Query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    collection: str | None = Field(None, title="Optional Qdrant collection name")


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []
    cached: bool = False
    latency_ms: float = 0.0


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    _api_key: str = Depends(verify_api_key),
):
    """
    Submit a question to the RAG AI Tutor.
    - Sanitizes input
    - Checks cache
    - Retrieves context from Qdrant
    - Generates answer via LLM
    """
    result = await run_rag(
        query=request.question,
        collection=request.collection
    )
    return QueryResponse(**result)
