from typing import Any, Dict, List, Optional
import math
from .base_store import BaseVectorStore

class InMemoryVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        self._items: List[Dict[str, Any]] = []

    def upsert_chunks(
        self,
        chunks: List[Any],
        dense_vectors: Optional[List[List[float]]] = None,
        sparse_vectors: Optional[List[Dict[str, float]]] = None,
    ) -> None:
        for i, chunk in enumerate(chunks):
            item = {
                "payload": chunk if isinstance(chunk, dict) else chunk.model_dump(),
                "dense_vector": dense_vectors[i] if dense_vectors else None,
                "sparse_vector": sparse_vectors[i] if sparse_vectors else None,
            }
            self._items.append(item)

    def search_dense(
        self, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        for item in self._items:
            if not self._matches(item["payload"], filters): continue
            if not item["dense_vector"]: continue
            
            score = self._cosine_sim(query_embedding, item["dense_vector"])
            results.append({"score": score, "payload": item["payload"]})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search_sparse(
        self, query_sparse: Dict[str, float], top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        for item in self._items:
            if not self._matches(item["payload"], filters): continue
            if not item["sparse_vector"]: continue
            
            score = sum(query_sparse.get(k, 0) * v for k, v in item["sparse_vector"].items())
            results.append({"score": score, "payload": item["payload"]})
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _matches(self, payload: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        if not filters: return True
        meta = payload.get("metadata", {})
        return all(payload.get(k) == v or meta.get(k) == v for k, v in filters.items())

    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        mag = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
        return dot / mag if mag > 0 else 0.0