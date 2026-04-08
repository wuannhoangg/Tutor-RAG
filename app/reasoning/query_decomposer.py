"""
Deterministic query decomposition for complex user queries.
"""

from __future__ import annotations

import re
from typing import List

from .query_classifier import classify_query


def _clean(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _extract_comparison_pair(query: str) -> tuple[str, str] | tuple[None, None]:
    patterns = [
        r"(?:compare|so sánh)\s+(.+?)\s+(?:and|và|vs|versus)\s+(.+)",
        r"difference between\s+(.+?)\s+and\s+(.+)",
        r"khác nhau giữa\s+(.+?)\s+và\s+(.+)",
        r"(.+?)\s+(?:vs|versus)\s+(.+)",
    ]

    cleaned = _clean(query)

    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            left = _clean(match.group(1))
            right = _clean(match.group(2))
            if left and right:
                return left, right

    return None, None


def decompose_query(query: str) -> List[str]:
    """
    Break a complex query into smaller retrievable sub-questions.
    """
    cleaned = _clean(query)
    if not cleaned:
        return []

    label = classify_query(cleaned)

    if label != "DECOMPOSITION_REQUIRED":
        return [cleaned]

    left, right = _extract_comparison_pair(cleaned)
    if left and right:
        return _dedupe_keep_order(
            [
                f"What is {left}?",
                f"What is {right}?",
                f"What are the defining properties of {left}?",
                f"What are the defining properties of {right}?",
                f"What are the key differences between {left} and {right}?",
            ]
        )

    parts = re.split(r"\?+|;+|\b(?:and|và|đồng thời)\b", cleaned, flags=re.IGNORECASE)
    parts = [_clean(part) for part in parts if _clean(part)]

    if len(parts) >= 2:
        return _dedupe_keep_order(parts[:5])

    lower = cleaned.lower()

    if "why" in lower or "tại sao" in lower:
        return _dedupe_keep_order(
            [
                f"What concepts are involved in: {cleaned}?",
                f"What evidence in the material explains: {cleaned}?",
                f"What supporting details or conditions are mentioned for: {cleaned}?",
            ]
        )

    if "how" in lower or "như thế nào" in lower:
        return _dedupe_keep_order(
            [
                f"What are the main concepts required to answer: {cleaned}?",
                f"What steps or process details are mentioned for: {cleaned}?",
                f"What evidence in the material supports the process for: {cleaned}?",
            ]
        )

    return [
        cleaned,
    ]