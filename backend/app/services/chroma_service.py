"""Chroma vector store service — Phase 2 upgrade.

Provides a singleton persistent collection with metadata filtering support.
"""
from typing import Any, Optional
import chromadb
from chromadb.config import Settings
from app.config import get_settings

settings = get_settings()

_client: Optional[Any] = None
COLLECTION_NAME = "resumepilot"


def get_client() -> Any:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
    return _client


def get_collection():
    """Get or create the single ResumePilot collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine distance for normalized vectors
    )


def reset_collection():
    """Delete and recreate the collection. Used during re-indexing."""
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection()


def collection_count() -> int:
    return get_collection().count()
