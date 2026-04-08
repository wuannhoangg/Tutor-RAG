"""
Deterministic query classification for the reasoning pipeline.
Runs without an LLM client and can be replaced later if needed.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

_LABEL_FACTUAL = "FACTUAL_QA"
_LABEL_DECOMPOSE = "DECOMPOSITION_REQUIRED"
_LABEL_CHAT = "GENERAL_CHAT"
_LABEL_OOS = "OUT_OF_SCOPE"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _count_question_marks(text: str) -> int:
    return text.count("?") + text.count("？")


def classify_query_with_reason(query: str, context: Optional[str] = None) -> Dict[str, str]:
    """
    Return a structured classification result with a brief reason.
    """
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
        "latest news",
        "thời tiết",
        "weather",
        "stock price",
        "giá cổ phiếu",
        "bóng đá",
        "football score",
        "president",
        "chính trị",
        "movie showtimes",
        "đặt lịch",
        "send email",
        "mua hàng",
    ]
    if any(keyword in q for keyword in out_of_scope_keywords):
        return {
            "label": _LABEL_OOS,
            "reason": "Query appears unrelated to grounded study-material QA.",
        }

    decomposition_cues = [
        "compare",
        "comparison",
        "so sánh",
        "khác nhau",
        "difference between",
        "advantages and disadvantages",
        "ưu điểm và nhược điểm",
        "why",
        "tại sao",
        "how",
        "như thế nào",
        "versus",
        " vs ",
        "phân tích",
        "explain why",
        "step by step",
    ]

    multiple_clause_cues = [
        " and ",
        " cùng với ",
        " đồng thời ",
        ";",
        ", and ",
    ]

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


def classify_query(query: str, context: Optional[str] = None) -> str:
    """
    Backward-compatible simple classifier returning only the label.
    """
    return classify_query_with_reason(query=query, context=context)["label"]