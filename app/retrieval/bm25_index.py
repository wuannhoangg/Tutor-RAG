from typing import Any, Dict, List, Optional
import re
from rank_bm25 import BM25Okapi

class BM25Index:
    """
    In-memory BM25 index for sparse retrieval using rank_bm25.
    """

    def __init__(self) -> None:
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def _tokenize(self, text: str) -> List[str]:
        # Tách từ đơn giản, có thể nâng cấp lên underthesea/pyvi cho tiếng Việt sau này
        return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

    def add_chunks(self, chunks: List[Any]) -> None:
        """
        Add new chunks to the index and rebuild the BM25 model.
        """
        for chunk in chunks:
            payload = chunk if isinstance(chunk, dict) else chunk.model_dump()
            self.corpus_chunks.append(payload)
            self.tokenized_corpus.append(self._tokenize(payload.get("text", "")))
        
        # Build lại index khi có chunk mới
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(
        self, query_text: str, top_k: int, filters: Optional[Dict[str, Any]] = None
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

            # Áp dụng Metadata filters
            if filters:
                meta = payload.get("metadata", {})
                match = all(payload.get(k) == v or meta.get(k) == v for k, v in filters.items())
                if not match:
                    continue

            results.append({"score": float(score), "payload": payload})

        # Sắp xếp điểm BM25 giảm dần
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        # Normalization (0 -> 1) để tương thích với Dense Score trong Hybrid Retriever
        if results:
            max_score = results[0]["score"]
            for res in results:
                res["score"] = res["score"] / max_score if max_score > 0 else 0.0

        return results