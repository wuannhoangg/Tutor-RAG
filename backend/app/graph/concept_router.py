from __future__ import annotations

import re
import json
import asyncio
from typing import Optional

from app.core.llm_client import LLMClient
from app.prompts.graph_prompts import build_concept_router_prompt
from app.core.provider_config import resolve_llm_config
from app.schemas.llm_config import LLMConfig

def _clean_concept(concept: str) -> str:
    clean = re.sub(r"\s+", " ", (concept or "").strip())
    return clean.title() if clean else ""

def _route_concept_deterministic(query: str) -> str:
    """
    Fallback logic: Bắt các từ viết tắt hoặc cụm từ viết hoa trong câu hỏi.
    """
    if not query.strip():
        return ""

    acronyms = re.findall(r"\b[A-Z]{2,}\b", query)
    if acronyms:
        return _clean_concept(acronyms[0])
    
    capitalized_phrases = re.findall(r"\b[A-ZÀ-Ỹ][a-zà-ỹ]+\s[A-ZÀ-Ỹ][a-zà-ỹ]+\b", query)
    if capitalized_phrases:
        return _clean_concept(capitalized_phrases[0])
        
    return ""

async def route_concept_async(
    query: str, 
    user_llm_config: Optional[LLMConfig] = None
) -> str:
    """
    Sử dụng LLM để xác định trọng tâm (concept) của câu hỏi.
    """
    if not query.strip():
        return ""

    resolved = resolve_llm_config(user_llm_config)
    client = LLMClient(resolved)
    prompt = build_concept_router_prompt(query=query)
    
    messages = [
        {"role": "system", "content": "You are a concept router. Output JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "target_concept" in result and isinstance(result["target_concept"], str):
                return _clean_concept(result["target_concept"])
        except json.JSONDecodeError:
            pass

    return _route_concept_deterministic(query)

def route_concept(query: str, user_llm_config: Optional[LLMConfig] = None) -> str:
    """Wrapper đồng bộ."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(route_concept_async(query, user_llm_config))
    else:
        return asyncio.run(route_concept_async(query, user_llm_config))