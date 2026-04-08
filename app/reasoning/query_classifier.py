from __future__ import annotations

import re
import json
import asyncio
from typing import Any, Dict, Optional

from app.core.llm_client import LLMClient
from app.prompts.reasoning_prompts import build_query_classifier_prompt

_LABEL_FACTUAL = "FACTUAL_QA"
_LABEL_DECOMPOSE = "DECOMPOSITION_REQUIRED"
_LABEL_CHAT = "GENERAL_CHAT"
_LABEL_OOS = "OUT_OF_SCOPE"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _count_question_marks(text: str) -> int:
    return text.count("?") + text.count("？")


def _classify_query_deterministic(query: str, context: Optional[str] = None) -> Dict[str, str]:
    """Fallback logic when LLM is unavailable."""
    q = _normalize(query)

    if not q:
        return {
            "label": _LABEL_CHAT,
            "reason": "Empty input is treated as conversational or non-task input.",
        }

    greeting_patterns = [
        r"^(hi|hello|hey|yo)\b",
        r"^(xin chào|chào|helo)\b",
        r"^(good morning|good afternoon|good evening)\b",
        r"^(cảm ơn|thanks|thank you)\b",
    ]
    if any(re.search(pattern, q) for pattern in greeting_patterns):
        if len(q.split()) <= 8:
            return {
                "label": _LABEL_CHAT,
                "reason": "Short greeting or conversational input.",
            }

    out_of_scope_keywords = [
        "latest news", "thời tiết", "weather", "stock price", "giá cổ phiếu",
        "bóng đá", "football score", "president", "chính trị", "movie showtimes",
        "đặt lịch", "send email", "mua hàng",
    ]
    if any(keyword in q for keyword in out_of_scope_keywords):
        return {
            "label": _LABEL_OOS,
            "reason": "Query appears unrelated to grounded study-material QA.",
        }

    decomposition_cues = [
        "compare", "comparison", "so sánh", "khác nhau", "difference between",
        "advantages and disadvantages", "ưu điểm và nhược điểm", "why", "tại sao",
        "how", "như thế nào", "versus", " vs ", "phân tích", "explain why", "step by step",
    ]

    multiple_clause_cues = [" and ", " cùng với ", " đồng thời ", ";", ", and "]

    if _count_question_marks(query) >= 2:
        return {
            "label": _LABEL_DECOMPOSE,
            "reason": "Multiple explicit questions detected.",
        }

    if any(cue in q for cue in decomposition_cues):
        return {
            "label": _LABEL_DECOMPOSE,
            "reason": "Query likely requires multi-step reasoning or comparison.",
        }

    if len(q.split()) > 22 and any(cue in q for cue in multiple_clause_cues):
        return {
            "label": _LABEL_DECOMPOSE,
            "reason": "Long query with multiple clauses is better decomposed first.",
        }

    return {
        "label": _LABEL_FACTUAL,
        "reason": "Single focused information request.",
    }


async def classify_query_with_reason_async(
    query: str, 
    context: Optional[str] = None,
    user_api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Try LLM first. If it fails, fallback to deterministic logic.
    """
    client = LLMClient(user_api_key=user_api_key)
    
    prompt = build_query_classifier_prompt(query=query, context=context)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs strictly in JSON."},
        {"role": "user", "content": prompt}
    ]
    
    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "label" in result and "reason" in result:
                return result
        except json.JSONDecodeError:
            pass 
            
    return _classify_query_deterministic(query, context)


def classify_query_with_reason(
    query: str, 
    context: Optional[str] = None,
    user_api_key: Optional[str] = None
) -> Dict[str, str]:
    """Synchronous wrapper for backward compatibility."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(classify_query_with_reason_async(query, context, user_api_key))
    else:
        return asyncio.run(classify_query_with_reason_async(query, context, user_api_key))


def classify_query(
    query: str, 
    context: Optional[str] = None,
    user_api_key: Optional[str] = None
) -> str:
    """Backward-compatible simple classifier."""
    result = classify_query_with_reason(query=query, context=context, user_api_key=user_api_key)
    
    if asyncio.isfuture(result) or asyncio.istask(result):
        # If inside a running loop and returning a Task, fallback safely
        return _classify_query_deterministic(query, context)["label"]
        
    return result["label"]