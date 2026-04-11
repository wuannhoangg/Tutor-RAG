from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import logging
from app.retrieval.embedder import Embedder
from app.retrieval.base_store import BaseVectorStore


logger = logging.logger.getChild("dense_retriever")


class DenseRetriever:
    """
    Dense vector similarity retrieval.
    """

    def __init__(self, embedder: Embedder, vector_store: BaseVectorStore) -> None:
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

        query_embedding = self.embedder.embed_query(query_text)
        return self.vector_store.search_dense(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters or {},
        )