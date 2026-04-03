"""
ingestion/document_loader.py — Parse PDF, DOCX, and TXT to plain text.
"""

import io
import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def load_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PDF appears to be empty or scanned (no extractable text).",
            )
        return text
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PDF parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse PDF: {exc}",
        )


def load_docx(content: bytes) -> str:
    """Extract text from a DOCX file."""
    try:
        import docx

        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="DOCX file appears to be empty.",
            )
        return text
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("DOCX parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse DOCX: {exc}",
        )


def load_txt(content: bytes) -> str:
    """Decode a plain text file."""
    try:
        text = content.decode("utf-8", errors="replace").strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TXT file is empty.",
            )
        return text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to decode TXT: {exc}",
        )


MIME_TO_LOADER = {
    "application/pdf": load_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": load_docx,
    "text/plain": load_txt,
}


def load_document(content: bytes, mime_type: str) -> str:
    """Dispatch to the correct loader based on MIME type."""
    loader = MIME_TO_LOADER.get(mime_type)
    if not loader:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported MIME type: {mime_type}",
        )
    return loader(content)
