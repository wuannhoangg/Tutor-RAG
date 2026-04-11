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

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        fallback_dim: int = 128,
    ) -> None:
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self.output_dim = fallback_dim
        self.model = None

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.model = SentenceTransformer(model_name)

            try:
                self.output_dim = int(self.model.get_sentence_embedding_dimension())
            except Exception:
                probe = self.model.encode(
                    ["query: dimension_probe"],
                    convert_to_tensor=False,
                    normalize_embeddings=True,
                )
                self.output_dim = len(probe[0])

            logger.info("Loaded SentenceTransformer model: %s", model_name)
        except Exception as exc:
            logger.warning("Falling back to hash embedding. Reason: %s", exc)
            self.model = None
            self.output_dim = fallback_dim

    def get_output_dim(self) -> int:
        return int(self.output_dim)

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

    def _prepare_document(self, text: str) -> str:
        return f"passage: {text}"

    def _prepare_query(self, text: str) -> str:
        return f"query: {text}"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.model is not None:
            prepared = [self._prepare_document(text) for text in texts]
            embeddings = self.model.encode(
                prepared,
                convert_to_tensor=False,
                normalize_embeddings=True,
            )
            return embeddings.tolist()

        return [self._hash_embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        if self.model is not None:
            prepared = self._prepare_query(text)
            return self.model.encode(
                [prepared],
                convert_to_tensor=False,
                normalize_embeddings=True,
            )[0].tolist()

        return self._hash_embed(text)

    # Backward-compatible aliases
    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)

    def embed_chunk(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]