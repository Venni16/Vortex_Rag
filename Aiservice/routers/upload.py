"""
routers/upload.py — Endpoints for document and URL ingestion.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, HttpUrl

import httpx

from config import get_settings
from ingestion.background_worker import get_job_status, ingest_document, _set_job_status
from ingestion.document_loader import load_document
from ingestion.web_scraper import scrape_url
from security.auth import verify_api_key
from security.validators import validate_file, validate_url

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/upload", tags=["Ingestion"])


class UrlRequest(BaseModel):
    url: HttpUrl
    collection: str | None = None
    deep_scrape: bool = False  # If true, crawls level-1 sub-links


@router.post("/doc", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str | None = Form(None),
    _api_key: str = Depends(verify_api_key),
):
    """
    Upload a PDF, DOCX, or TXT file for ingestion.
    Validation happens synchronously; ingestion happens in background.
    """
    # 1. Basic validation (MIME + size)
    content = await validate_file(file)

    # 2. Extract text (inline but fast)
    text = load_document(content, file.content_type)

    # 3. Schedule background job (Chunking, Embedding, Vector Upsert)
    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        ingest_document,
        content=text,
        source_id=file.filename,
        collection=collection,
        job_id=job_id,
    )

    await _set_job_status(job_id, "queued", f"Processing file: {file.filename}")

    return {
        "job_id": job_id,
        "status": "queued",
        "detail": f"Processing file: {file.filename}",
        "collection": collection or settings.QDRANT_COLLECTION
    }


@router.post("/url", status_code=status.HTTP_202_ACCEPTED)
async def upload_url(
    background_tasks: BackgroundTasks,
    request: UrlRequest,
    _api_key: str = Depends(verify_api_key),
):
    """
    Submit a URL for web scraping and ingestion.
    URL check happens synchronously; scraping and ingestion in background.
    If deep_scrape is True, it also crawls and ingests level-1 links.
    """
    from ingestion.web_scraper import get_links
    
    # 1. SSRF check + URL scheme check
    target_url = validate_url(str(request.url))

    # 2. Schedule background job
    job_id = str(uuid.uuid4())

    async def _recursive_scrape_and_ingest():
        try:
            # A. Scrape main page
            html_raw = ""
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(target_url, follow_redirects=True)
                resp.raise_for_status()
                html_raw = resp.text

            main_text = await scrape_url(target_url)
            await ingest_document(main_text, target_url, request.collection, job_id)
            
            # B. If deep_scrape, find and process sub-links
            if request.deep_scrape:
                links = get_links(html_raw, target_url)
                logger.info("[job:%s] Deep scrape: found %d sub-links for %s", job_id, len(links), target_url)
                
                for link in links[:20]:  # Limit to 20 sub-links for safety
                    try:
                        sub_text = await scrape_url(link)
                        await ingest_document(sub_text, link, request.collection, job_id)
                    except Exception as e:
                        logger.warning("Deep scrape failed for sub-link %s: %s", link, e)
            
            await _set_job_status(job_id, "completed", f"Ingested {target_url} and its sub-links.")
        except Exception as exc:
            logger.error("Scrape/Ingest failed for %s: %s", target_url, exc)
            await _set_job_status(job_id, "failed", str(exc))

    background_tasks.add_task(_recursive_scrape_and_ingest)

    detail_msg = f"Scraping {'(deep) ' if request.deep_scrape else ''}URL: {target_url}"
    await _set_job_status(job_id, "queued", detail_msg)

    return {
        "job_id": job_id,
        "status": "queued",
        "detail": detail_msg,
        "collection": request.collection or settings.QDRANT_COLLECTION
    }


@router.get("/status/{job_id}")
async def check_job_status(job_id: str):
    """Poll for the status of an ingestion job."""
    status_data = await get_job_status(job_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job ID {job_id} not found."
        )
    return status_data
