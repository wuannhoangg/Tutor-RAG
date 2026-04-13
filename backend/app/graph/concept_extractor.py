from __future__ import annotations

import re
import json
import asyncio
from typing import List, Optional

from app.core.llm_client import LLMClient
from app.prompts.graph_prompts import build_concept_extractor_prompt
from app.core.provider_config import resolve_llm_config, resolve_ingestion_llm_config
from app.schemas.llm_config import LLMConfig

def _clean_concept(concept: str) -> str:
    """Chuẩn hóa concept: viết hoa chữ đầu, bỏ khoảng trắng thừa."""
    clean = re.sub(r"\s+", " ", (concept or "").strip())
    return clean.title() if clean else ""

def _extract_concepts_deterministic(text: str) -> List[str]:
    """
    Fallback logic: Trích xuất các cụm từ viết hoa (VD: Machine Learning) 
    và các từ viết tắt (VD: RAG, BCNF) bằng Regex.
    """
    if not text.strip():
        return []

    acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
    capitalized_phrases = re.findall(r"\b[A-ZÀ-Ỹ][a-zà-ỹ]+\s[A-ZÀ-Ỹ][a-zà-ỹ]+\b", text)
    
    raw_concepts = acronyms + capitalized_phrases
    
    seen = set()
    results = []
    for c in raw_concepts:
        cleaned = _clean_concept(c)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            results.append(cleaned)
            
    return results[:5] 

async def extract_concepts_async(
    text: str, 
    user_llm_config: Optional[LLMConfig] = None
) -> List[str]:
    """Sử dụng LLM để đọc hiểu và trích xuất khái niệm."""
    if not text.strip():
        return []

    if user_llm_config is None or user_llm_config.mode == "platform_default":
        resolved = resolve_ingestion_llm_config()
    else:
        resolved = resolve_llm_config(user_llm_config)
    client = LLMClient(resolved)
    
    prompt = build_concept_extractor_prompt(text=text)
    
    messages = [
        {"role": "system", "content": "You are a specialized concept extractor. Output JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "concepts" in result and isinstance(result["concepts"], list):
                concepts = [_clean_concept(c) for c in result["concepts"]]
                return [c for c in concepts if c]
        except json.JSONDecodeError:
            pass

    return _extract_concepts_deterministic(text)

def extract_concepts(text: str, user_llm_config: Optional[LLMConfig] = None) -> List[str]:
    """Wrapper đồng bộ."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(extract_concepts_async(text, user_llm_config))
    else:
        return asyncio.run(extract_concepts_async(text, user_llm_config))