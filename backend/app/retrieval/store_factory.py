from __future__ import annotations

from typing import Optional

from app.core import logging
from app.core.config import get_settings

from .base_store import BaseVectorStore
from .in_memory_store import InMemoryVectorStore
from .qdrant_store import QdrantVectorStore

logger = logging.logger.getChild("store_factory")


def get_vector_store(
    vector_size: Optional[int] = None,
    collection_name: Optional[str] = None,
) -> BaseVectorStore:
    settings = get_settings()

    qdrant_cloud_enabled = bool(settings.QDRANT_URL)
    qdrant_local_enabled = bool(settings.VECTOR_STORE_HOST) and settings.VECTOR_STORE_PORT is not None
    should_try_qdrant = qdrant_cloud_enabled or qdrant_local_enabled

    if should_try_qdrant:
        try:
            return QdrantVectorStore(
                collection_name=collection_name or settings.QDRANT_COLLECTION_NAME,
                vector_size=vector_size or 1024,
            )
        except Exception as exc:
            logger.warning("Falling back to in-memory vector store: %s", exc)
            return InMemoryVectorStore()

    logger.info("Qdrant is not configured. Using in-memory vector store.")
    return InMemoryVectorStore()