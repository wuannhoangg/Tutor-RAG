from __future__ import annotations

import re
from typing import Any, Dict, List

from app.core import logging


logger = logging.logger.getChild("reranker")


class Reranker:
    """
    Deterministic reranker using lexical overlap.
    """

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

    def re_rank(self, candidates: List[Dict[str, Any]], query_text: str, top_k: int) -> List[Dict[str, Any]]:
        query_tokens = set(self._tokenize(query_text))

        reranked: List[Dict[str, Any]] = []
        for candidate in candidates:
            payload = candidate.get("payload", {}) or {}
            text = payload.get("text", "")
            text_tokens = set(self._tokenize(text))
            overlap = len(query_tokens & text_tokens)
            boosted_score = float(candidate.get("score", 0.0)) + (0.05 * overlap)

            item = dict(candidate)
            item["score"] = boosted_score
            reranked.append(item)

        reranked.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return reranked[:top_k]