from __future__ import annotations

import re
import json
import asyncio
from typing import Any, Dict, List, Optional

from app.core.llm_client import LLMClient
from app.prompts.verification_prompts import build_claim_checker_prompt
from app.schemas.llm_config import LLMConfig
from app.core.provider_config import resolve_llm_config

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ỹ0-9_]+", (text or "").lower())

def _check_claim_deterministic(claim: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback lexical check."""
    if not claim.strip():
        return {"is_supported": False, "support_evidence": "Empty claim.", "reasoning": "No text."}

    claim_tokens = set(_tokenize(claim))
    best_overlap, best_excerpt = 0, ""

    for chunk in context_chunks or []:
        text = chunk.get("text") or chunk.get("snippet") or ""
        tokens = set(_tokenize(text))
        overlap = len(claim_tokens & tokens)
        if overlap > best_overlap:
            best_overlap, best_excerpt = overlap, text[:300]

    threshold = max(2, min(6, len(claim_tokens) // 4 + 1))
    is_supported = best_overlap >= threshold

    return {
        "is_supported": is_supported,
        "support_evidence": best_excerpt if is_supported else "Insufficient evidence.",
        "reasoning": "Lexical overlap fallback check."
    }

async def check_claim_async(
    claim: str, 
    context_chunks: List[Dict[str, Any]],
    user_config: Optional[LLMConfig] = None
) -> Dict[str, Any]:
    if not claim.strip():
        return {"is_supported": False, "support_evidence": "Empty.", "reasoning": "Empty."}

    resolved = resolve_llm_config(user_config)
    client = LLMClient(resolved)
    
    prompt = build_claim_checker_prompt(claim=claim, context_chunks=context_chunks)
    
    messages = [
        {"role": "system", "content": "You are a factual claim checker. Output JSON."},
        {"role": "user", "content": prompt}
    ]
    
    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            return json.loads(llm_response)
        except json.JSONDecodeError:
            pass

    return _check_claim_deterministic(claim, context_chunks)

def check_claim(claim: str, context_chunks: List[Dict[str, Any]], user_config: Optional[LLMConfig] = None) -> Dict[str, Any]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(check_claim_async(claim, context_chunks, user_config))
    else:
        return asyncio.run(check_claim_async(claim, context_chunks, user_config))