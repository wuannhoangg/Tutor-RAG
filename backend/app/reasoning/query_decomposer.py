from __future__ import annotations

import re
import json
import asyncio
from typing import List, Optional

from app.core.llm_client import LLMClient
from app.prompts.reasoning_prompts import build_query_decomposer_prompt
from .query_classifier import _classify_query_deterministic
from app.schemas.llm_config import LLMConfig
from app.core.provider_config import resolve_llm_config


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


def _decompose_query_deterministic(query: str) -> List[str]:
    """Fallback logic when LLM is unavailable."""
    cleaned = _clean(query)
    if not cleaned:
        return []

    label = _classify_query_deterministic(cleaned)["label"]

    if label != "DECOMPOSITION_REQUIRED":
        return [cleaned]

    left, right = _extract_comparison_pair(cleaned)
    if left and right:
        return _dedupe_keep_order([
            f"What is {left}?",
            f"What is {right}?",
            f"What are the defining properties of {left}?",
            f"What are the defining properties of {right}?",
            f"What are the key differences between {left} and {right}?",
        ])

    parts = re.split(r"\?+|;+|\b(?:and|và|đồng thời)\b", cleaned, flags=re.IGNORECASE)
    parts = [_clean(part) for part in parts if _clean(part)]

    if len(parts) >= 2:
        return _dedupe_keep_order(parts[:5])

    lower = cleaned.lower()
    if "why" in lower or "tại sao" in lower:
        return _dedupe_keep_order([
            f"What concepts are involved in: {cleaned}?",
            f"What evidence in the material explains: {cleaned}?",
            f"What supporting details or conditions are mentioned for: {cleaned}?",
        ])

    if "how" in lower or "như thế nào" in lower:
        return _dedupe_keep_order([
            f"What are the main concepts required to answer: {cleaned}?",
            f"What steps or process details are mentioned for: {cleaned}?",
            f"What evidence in the material supports the process for: {cleaned}?",
        ])

    return [cleaned]


async def decompose_query_async(query: str, user_config: Optional[LLMConfig] = None) -> List[str]:
    """Try LLM first for intelligent decomposition."""
    cleaned = _clean(query)
    if not cleaned:
        return []

    resolved = resolve_llm_config(user_config)
    client = LLMClient(resolved)
    
    prompt = build_query_decomposer_prompt(query=cleaned)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs strictly in JSON."},
        {"role": "user", "content": prompt}
    ]

    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "sub_questions" in result:
                return result["sub_questions"]
        except json.JSONDecodeError:
            pass

    return _decompose_query_deterministic(query)


def decompose_query(query: str, user_config: Optional[LLMConfig] = None) -> List[str]:
    """Synchronous wrapper for backward compatibility."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(decompose_query_async(query, user_config))
    else:
        return asyncio.run(decompose_query_async(query, user_config))