from __future__ import annotations

import re
from typing import Any, Dict, List


def _normalize_chunks(context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for chunk in context_chunks or []:
        metadata = chunk.get("metadata", {}) or {}
        normalized.append(
            {
                "text": chunk.get("text") or chunk.get("snippet") or "",
                "metadata": metadata,
            }
        )
    return normalized


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())


def _best_support(sentence: str, chunks: List[Dict[str, Any]]) -> tuple[bool, str]:
    sentence_tokens = set(_tokenize(sentence))
    if not sentence_tokens:
        return True, ""

    best_overlap = 0
    best_excerpt = ""

    for chunk in chunks:
        text = chunk["text"]
        chunk_tokens = set(_tokenize(text))
        overlap = len(sentence_tokens & chunk_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_excerpt = text[:300]

    threshold = max(2, min(6, len(sentence_tokens) // 4 + 1))
    return best_overlap >= threshold, best_excerpt


def verify_answer(answer_to_verify: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministically verify whether the answer is supported by retrieved context.
    """
    chunks = _normalize_chunks(context_chunks)
    if not answer_to_verify.strip():
        return {
            "is_supported": False,
            "reasoning": "Answer is empty.",
            "corrected_answer": "The provided material is insufficient to answer this question.",
        }

    if not chunks:
        return {
            "is_supported": False,
            "reasoning": "No context chunks were provided for verification.",
            "corrected_answer": "The provided material is insufficient to answer this question.",
        }

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer_to_verify.strip()) if part.strip()]
    unsupported: List[str] = []

    for sentence in sentences:
        supported, _ = _best_support(sentence, chunks)
        if not supported:
            unsupported.append(sentence)

    if unsupported:
        return {
            "is_supported": False,
            "reasoning": f"{len(unsupported)} sentence(s) appear insufficiently supported.",
            "corrected_answer": "The provided material is insufficient to answer this question.",
        }

    return {
        "is_supported": True,
        "reasoning": "The answer is sufficiently grounded in the retrieved context.",
        "corrected_answer": answer_to_verify,
    }