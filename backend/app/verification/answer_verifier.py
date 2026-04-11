from __future__ import annotations

import re
import json
import asyncio
from typing import Any, Dict, List, Optional

from app.core.llm_client import LLMClient
from app.prompts.verification_prompts import build_answer_verifier_prompt
from app.schemas.llm_config import LLMConfig
from app.core.provider_config import resolve_llm_config

def _normalize_chunks(context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for chunk in context_chunks or []:
        metadata = chunk.get("metadata", {}) or {}
        normalized.append({
            "text": chunk.get("text") or chunk.get("snippet") or "",
            "metadata": metadata,
        })
    return normalized

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

def _best_support(sentence: str, chunks: List[Dict[str, Any]]) -> tuple[bool, str]:
    sentence_tokens = set(_tokenize(sentence))
    if not sentence_tokens: return True, ""
    best_overlap, best_excerpt = 0, ""
    for chunk in chunks:
        text = chunk["text"]
        chunk_tokens = set(_tokenize(text))
        overlap = len(sentence_tokens & chunk_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_excerpt = text[:300]
    threshold = max(2, min(6, len(sentence_tokens) // 4 + 1))
    return best_overlap >= threshold, best_excerpt

def _verify_answer_deterministic(answer_to_verify: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Logic cũ dựa trên lexical overlap (Fallback)."""
    chunks = _normalize_chunks(context_chunks)
    if not answer_to_verify.strip():
        return {"is_supported": False, "reasoning": "Answer is empty.", "corrected_answer": ""}
    
    if not chunks:
        return {"is_supported": False, "reasoning": "No context chunks provided.", "corrected_answer": ""}

    sentences = [p.strip() for p in re.split(r"(?<=[.!?])\s+", answer_to_verify.strip()) if p.strip()]
    unsupported = [s for s in sentences if not _best_support(s, chunks)[0]]

    if unsupported:
        return {
            "is_supported": False, 
            "reasoning": f"{len(unsupported)} sentence(s) lack lexical support.",
            "corrected_answer": "The provided material is insufficient to answer this question."
        }
    return {"is_supported": True, "reasoning": "Sufficient lexical grounding.", "corrected_answer": answer_to_verify}

async def verify_answer_async(
    answer_to_verify: str, 
    context_chunks: List[Dict[str, Any]],
    user_config: Optional[LLMConfig] = None
) -> Dict[str, Any]:
    """Sử dụng LLM để kiểm chứng tính xác thực."""
    if not answer_to_verify.strip():
        return {"is_supported": False, "reasoning": "Empty answer.", "corrected_answer": ""}

    resolved = resolve_llm_config(user_config)
    client = LLMClient(resolved)
    
    prompt = build_answer_verifier_prompt(context_chunks=context_chunks, answer_to_verify=answer_to_verify)
    
    messages = [
        {"role": "system", "content": "You are a strict factual verifier. Output strictly valid JSON."},
        {"role": "user", "content": prompt}
    ]
    
    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "is_supported" in result:
                return result
        except json.JSONDecodeError:
            pass

    return _verify_answer_deterministic(answer_to_verify, context_chunks)

def verify_answer(answer_to_verify: str, context_chunks: List[Dict[str, Any]], user_config: Optional[LLMConfig] = None) -> Dict[str, Any]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(verify_answer_async(answer_to_verify, context_chunks, user_config))
    else:
        return asyncio.run(verify_answer_async(answer_to_verify, context_chunks, user_config))