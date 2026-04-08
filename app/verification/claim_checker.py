from __future__ import annotations

import re
from typing import Any, Dict, List


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())


def check_claim(claim: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check whether a claim is supported by any retrieved chunk.
    """
    if not claim.strip():
        return {
            "is_supported": False,
            "support_evidence": "Empty claim.",
            "reasoning": "No claim text provided.",
        }

    claim_tokens = set(_tokenize(claim))
    best_overlap = 0
    best_excerpt = ""

    for chunk in context_chunks or []:
        text = chunk.get("text") or chunk.get("snippet") or ""
        chunk_tokens = set(_tokenize(text))
        overlap = len(claim_tokens & chunk_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_excerpt = text[:300]

    threshold = max(2, min(6, len(claim_tokens) // 4 + 1))
    is_supported = best_overlap >= threshold

    return {
        "is_supported": is_supported,
        "support_evidence": best_excerpt if best_excerpt else "Insufficient evidence.",
        "reasoning": (
            "Claim has enough lexical overlap with retrieved context."
            if is_supported
            else "Claim does not appear sufficiently supported by retrieved context."
        ),
    }