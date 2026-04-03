"""
ingestion/web_scraper.py — Sanitized async web scraper.

Performance optimisation:
- A single module-level httpx.AsyncClient is created once and reused across
  all scrape calls, eliminating TCP handshake + TLS overhead per request.
  Connection pool keeps up to 10 keep-alive connections.
- The client is initialised lazily on first use and exposed via get_http_client()
  so callers can await init_http_client() during app lifespan if desired.
"""

import logging

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RAGBot/1.0; +https://github.com/vortex-rag)"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
}

# Persistent connection pool — created once, reused for every scrape call.
# Eliminates per-request TCP handshake and TLS negotiation overhead.
_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return (or lazily create) the shared HTTP client."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            headers=_HEADERS,
            timeout=10.0,
            follow_redirects=True,
            max_redirects=3,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30,
            ),
        )
    return _http_client


async def close_http_client() -> None:
    """Close the shared HTTP client. Call during app shutdown."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


async def scrape_url(url: str, timeout: float = 10.0) -> str:
    """
    Fetch a URL and extract clean body text.
    - Reuses the module-level connection pool (no TCP handshake per call).
    - Strips scripts, styles, nav elements.
    - Returns plain text.
    """
    client = _get_client()
    try:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"URL timed out after {timeout}s: {url}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"URL returned HTTP {exc.response.status_code}: {url}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to fetch URL: {exc}",
        )

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"URL returned non-text content type: {content_type}",
        )

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    body = soup.find("body") or soup
    text = body.get_text(separator="\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No usable text found at the URL.",
        )

    logger.info("Scraped %d chars from %s", len(text), url)
    return text


def get_links(html_content: str, base_url: str) -> list[str]:
    """
    Extract all unique internal links from the HTML content.
    Only returns absolute URLs within the same domain.
    """
    from urllib.parse import urljoin, urlparse

    soup = BeautifulSoup(html_content, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = set()

    for a in soup.find_all("a", href=True):
        full_url = urljoin(base_url, a["href"])
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            if clean_url != base_url.rstrip("/"):
                links.add(clean_url)

    return list(links)
