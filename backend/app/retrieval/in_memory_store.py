from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, List, Optional

from .base_store import BaseVectorStore


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def _payload_from_chunk(self, chunk: Any) -> Dict[str, Any]:
        return chunk if isinstance(chunk, dict) else chunk.model_dump()

    def _chunk_key(self, payload: Dict[str, Any], index: int) -> str:
        metadata = payload.get("metadata", {}) or {}
        chunk_id = payload.get("chunk_id") or metadata.get("chunk_id")
        if chunk_id:
            return str(chunk_id)

        document_id = payload.get("document_id") or metadata.get("document_id") or "doc"
        text = payload.get("text", "")
        digest = hashlib.sha256(f"{document_id}:{index}:{text}".encode("utf-8")).hexdigest()
        return digest

    def upsert_chunks(
        self,
        chunks: List[Any],
        dense_vectors: Optional[List[List[float]]] = None,
        sparse_vectors: Optional[List[Dict[str, float]]] = None,
    ) -> None:
        if dense_vectors is not None and len(dense_vectors) != len(chunks):
            raise ValueError("dense_vectors length must match chunks length.")
        if sparse_vectors is not None and len(sparse_vectors) != len(chunks):
            raise ValueError("sparse_vectors length must match chunks length.")

        for i, chunk in enumerate(chunks):
            payload = self._payload_from_chunk(chunk)
            key = self._chunk_key(payload, i)

            self._items[key] = {
                "payload": payload,
                "dense_vector": dense_vectors[i] if dense_vectors else None,
                "sparse_vector": sparse_vectors[i] if sparse_vectors else None,
            }

    def search_dense(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for item in self._items.values():
            if not self._matches(item["payload"], filters):
                continue
            if not item["dense_vector"]:
                continue

            score = self._cosine_sim(query_embedding, item["dense_vector"])
            results.append({"score": score, "payload": item["payload"]})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search_sparse(
        self,
        query_sparse: Dict[str, float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for item in self._items.values():
            if not self._matches(item["payload"], filters):
                continue
            if not item["sparse_vector"]:
                continue

            score = sum(query_sparse.get(k, 0.0) * v for k, v in item["sparse_vector"].items())
            results.append({"score": score, "payload": item["payload"]})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _matches_value(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, list):
            if isinstance(expected, list):
                return any(item in actual for item in expected)
            return expected in actual
        return actual == expected

    def _matches(self, payload: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        if not filters:
            return True

        meta = payload.get("metadata", {}) or {}
        for key, expected in filters.items():
            actual = payload.get(key)
            meta_actual = meta.get(key)
            if self._matches_value(actual, expected) or self._matches_value(meta_actual, expected):
                continue
            return False
        return True

    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        mag = math.sqrt(sum(a * a for a in v1)) * math.sqrt(sum(b * b for b in v2))
        return dot / mag if mag > 0 else 0.0