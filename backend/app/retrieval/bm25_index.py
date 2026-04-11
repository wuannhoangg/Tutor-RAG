from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

from rank_bm25 import BM25Okapi


class BM25Index:
    """
    In-memory BM25 index for sparse retrieval using rank_bm25.
    """

    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

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

    def _rebuild(self) -> None:
        self.corpus_chunks = list(self._items.values())
        self.tokenized_corpus = [self._tokenize(item.get("text", "")) for item in self.corpus_chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus) if self.tokenized_corpus else None

    def add_chunks(self, chunks: List[Any]) -> None:
        for i, chunk in enumerate(chunks):
            payload = self._payload_from_chunk(chunk)
            key = self._chunk_key(payload, i)
            self._items[key] = payload
        self._rebuild()

    def _matches_value(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, list):
            if isinstance(expected, list):
                return any(item in actual for item in expected)
            return expected in actual
        return actual == expected

    def search(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.corpus_chunks:
            return []

        tokenized_query = self._tokenize(query_text)
        scores = self.bm25.get_scores(tokenized_query)

        results = []
        for i, score in enumerate(scores):
            if score <= 0:
                continue

            payload = self.corpus_chunks[i]

            if filters:
                meta = payload.get("metadata", {}) or {}
                matched = True
                for key, expected in filters.items():
                    if self._matches_value(payload.get(key), expected) or self._matches_value(meta.get(key), expected):
                        continue
                    matched = False
                    break
                if not matched:
                    continue

            results.append({"score": float(score), "payload": payload})

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        if results:
            max_score = results[0]["score"]
            for res in results:
                res["score"] = res["score"] / max_score if max_score > 0 else 0.0

        return results