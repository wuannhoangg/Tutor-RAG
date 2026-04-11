from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import logging
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.sparse_retriever import SparseRetriever


logger = logging.logger.getChild("hybrid_retriever")


class HybridRetriever:
    """
    Combine dense and sparse retrieval results.
    """

    def __init__(self, dense_retriever: DenseRetriever, sparse_retriever: SparseRetriever) -> None:
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever

    def _candidate_key(self, candidate: Dict[str, Any]) -> tuple:
        payload = candidate.get("payload", {}) or {}
        metadata = payload.get("metadata", {}) or {}
        return (
            payload.get("chunk_id") or metadata.get("chunk_id"),
            payload.get("document_id") or metadata.get("document_id"),
            payload.get("text"),
        )

    def retrieve(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        dense_results = self.dense_retriever.retrieve(query_text, top_k=top_k, filters=filters)
        sparse_results = self.sparse_retriever.retrieve(query_text, top_k=top_k, filters=filters)

        combined: Dict[tuple, Dict[str, Any]] = {}

        for source_name, results in (("dense", dense_results), ("sparse", sparse_results)):
            for item in results:
                key = self._candidate_key(item)
                existing = combined.get(key)

                if existing is None:
                    merged = dict(item)
                    merged["dense_score"] = float(item.get("score", 0.0)) if source_name == "dense" else 0.0
                    merged["sparse_score"] = float(item.get("score", 0.0)) if source_name == "sparse" else 0.0
                    combined[key] = merged
                else:
                    if source_name == "dense":
                        existing["dense_score"] = max(existing.get("dense_score", 0.0), float(item.get("score", 0.0)))
                    else:
                        existing["sparse_score"] = max(existing.get("sparse_score", 0.0), float(item.get("score", 0.0)))

        results = list(combined.values())
        for item in results:
            item["score"] = (
                0.6 * float(item.get("dense_score", 0.0))
                + 0.4 * float(item.get("sparse_score", 0.0))
            )

        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results[:top_k]