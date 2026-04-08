from __future__ import annotations

import math
import re
from typing import Dict, List


class SparseEncoder:
    """
    Sparse lexical encoder using normalized term frequency.
    """

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

    def encode(self, text: str) -> Dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}

        counts: Dict[str, float] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0.0) + 1.0

        norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
        return {k: v / norm for k, v in counts.items()}

    def encode_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        return [self.encode(text) for text in texts]