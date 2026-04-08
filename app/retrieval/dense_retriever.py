from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import logging
from app.retrieval.embedder import Embedder
from app.retrieval.vector_store import VectorStore


logger = logging.logger.getChild("dense_retriever")


class DenseRetriever:
    """
    Dense vector similarity retrieval.
    """

    def __init__(self, embedder: Embedder, vector_store: VectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            return []

        query_embedding = self.embedder.embed_chunk(query_text)
        results = self.vector_store.search_dense(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters or {},
        )
        return results