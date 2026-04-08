from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.retrieval.sparse_encoder import SparseEncoder
from app.retrieval.vector_store import VectorStore


class SparseRetriever:
    """
    Sparse lexical retrieval.
    """

    def __init__(self, encoder: SparseEncoder, vector_store: VectorStore) -> None:
        self.encoder = encoder
        self.vector_store = vector_store

    def retrieve(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            return []

        query_sparse = self.encoder.encode(query_text)
        return self.vector_store.search_sparse(
            query_sparse=query_sparse,
            top_k=top_k,
            filters=filters or {},
        )