from typing import Any, Dict, List, Optional
from app.retrieval.bm25_index import BM25Index

class SparseRetriever:
    """
    Sparse lexical retrieval using BM25.
    """

    def __init__(self, bm25_index: BM25Index) -> None:
        self.bm25_index = bm25_index

    def retrieve(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            return []

        return self.bm25_index.search(
            query_text=query_text,
            top_k=top_k,
            filters=filters or {},
        )