"""
security/validators.py — Input validation for files, URLs, and prompts.
"""

import ipaddress
import re
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile, status

from config import get_settings

settings = get_settings()

# ── Known prompt-injection patterns ───────────────────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore (all )?(previous|prior|above) instructions?", re.I),
    re.compile(r"disregard (all )?(previous|prior|above) instructions?", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"forget everything", re.I),
    re.compile(r"act as (a |an )?", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"<\|system\|>", re.I),
    re.compile(r"\[INST\]", re.I),
]

# ── Private / reserved IP ranges (SSRF guard) ─────────────────────────────────
_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_private_ip(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in _PRIVATE_NETS)
    except ValueError:
        # host is a domain name — we can't resolve here; allow it
        return False


# ── Public validators ──────────────────────────────────────────────────────────

async def validate_file(file: UploadFile) -> bytes:
    """
    Validates upload file:
    - MIME type must be in ALLOWED_MIME_TYPES
    - File size must not exceed MAX_FILE_SIZE_MB
    Returns raw bytes on success.
    """
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed: PDF, DOCX, TXT.",
        )

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB.",
        )
    return content


def validate_url(url: str) -> str:
    """
    Validates a URL for web ingestion:
    - Must be http or https
    - Must not point to private/reserved IP ranges (SSRF guard)
    Returns the cleaned URL on success.
    """
    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL must use http or https scheme.",
        )

    host = parsed.hostname or ""
    if not host:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL has no valid hostname.",
        )

    if _is_private_ip(host):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL not allowed: private/internal IP addresses are blocked.",
        )

    return url.strip()


def sanitize_prompt(text: str) -> str:
    """
    Strips common prompt-injection patterns from user input.
    Returns sanitized text. Raises 422 if injection is detected and severe.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Input contains disallowed content (prompt injection detected).",
            )
    # Strip null bytes and control characters
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return sanitized.strip()
