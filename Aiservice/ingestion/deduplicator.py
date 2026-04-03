"""
ingestion/deduplicator.py — Deterministic ID generation for chunks.
Ensures that identical text chunks translated to the same UUID, 
preventing duplicates in the vector store (upsert logic).
"""

import hashlib
import uuid


def generate_chunk_id(text: str, source_id: str) -> str:
    """
    Generate a deterministic UUID based on the text content and source.
    If the same text from the same source is ingested again, 
    the ID will be identical, allowing Qdrant to simply 'overwrite' it.
    """
    # Combine source_id and text to ensure uniqueness per source
    hasher = hashlib.sha256()
    hasher.update(source_id.encode("utf-8"))
    hasher.update(text.encode("utf-8"))
    
    # Create a version 5 UUID (deterministic from a namespace and a name)
    # We use a fixed DNS-like namespace for RAG chunks
    RAG_NAMESPACE = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    return str(uuid.uuid5(RAG_NAMESPACE, hasher.hexdigest()))
