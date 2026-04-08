from __future__ import annotations

import hashlib
import math
from typing import List

from app.core import logging


logger = logging.logger.getChild("embedder")


class Embedder:
    """
    Embedding wrapper with graceful fallback when sentence-transformers is unavailable.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", fallback_dim: int = 128) -> None:
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self.model = None

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.model = SentenceTransformer(model_name)
            logger.info("Loaded SentenceTransformer model: %s", model_name)
        except Exception as exc:
            logger.warning("Falling back to hash embedding. Reason: %s", exc)
            self.model = None

    def _hash_embed(self, text: str) -> List[float]:
        vector = [0.0] * self.fallback_dim
        tokens = [token for token in text.lower().split() if token.strip()]
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.fallback_dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.model is not None:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()

        return [self._hash_embed(text) for text in texts]

    def embed_chunk(self, text: str) -> List[float]:
        if self.model is not None:
            return self.model.encode([text], convert_to_tensor=False)[0].tolist()

        return self._hash_embed(text)