"""
ingestion/chunker.py — Word-boundary-aware sliding window text chunker.
"""

import re
from config import get_settings

settings = get_settings()


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """
    Split `text` into overlapping word-boundary chunks.

    Args:
        text:       The input text to split.
        chunk_size: Max number of words per chunk (default from config).
        overlap:    Number of words to carry over between chunks (default from config).

    Returns:
        A list of non-empty text strings.
    """
    size = chunk_size or settings.CHUNK_SIZE
    ovlp = overlap or settings.CHUNK_OVERLAP

    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()

    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += size - ovlp  # slide forward, keeping `overlap` words of context

    return chunks
