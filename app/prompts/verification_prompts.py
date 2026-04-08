"""
Prompt templates and helper builders for the Verification pipeline.
"""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any


def _stringify(value: Any) -> str:
    """
    Convert arbitrary Python objects into a prompt-friendly string.
    """
    if value is None:
        return "None"

    if isinstance(value, str):
        return value.strip()

    try:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(value)


ANSWER_VERIFIER_PROMPT = dedent(
    """
    You are a rigorous factual verifier for a grounded tutoring assistant.

    Your task:
    - Evaluate whether the hypothesized answer is fully supported by the context chunks.
    - Mark unsupported, speculative, or contradictory content as not supported.
    - Prefer caution over overclaiming.
    - If needed, provide a corrected answer using only supported evidence.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "is_supported": true,
        "reasoning": "brief explanation",
        "corrected_answer": "supported answer or empty string"
      }}

    Context Chunks:
    {context_chunks}

    Hypothesized Answer:
    {answer_to_verify}

    JSON:
    """
).strip()


CLAIM_CHECKER_PROMPT = dedent(
    """
    You are a claim support checker.

    Your task:
    - Determine whether the claim is supported by the provided context chunks.
    - If supported, identify the strongest supporting evidence.
    - If unsupported, say so clearly.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "is_supported": true,
        "support_evidence": "exact supporting quote or concise supported excerpt",
        "reasoning": "brief explanation"
      }}

    Claim:
    {claim}

    Context Chunks:
    {context_chunks}

    JSON:
    """
).strip()


def build_answer_verifier_prompt(context_chunks: Any, answer_to_verify: str) -> str:
    return ANSWER_VERIFIER_PROMPT.format(
        context_chunks=_stringify(context_chunks),
        answer_to_verify=(answer_to_verify or "").strip(),
    )


def build_claim_checker_prompt(claim: str, context_chunks: Any) -> str:
    return CLAIM_CHECKER_PROMPT.format(
        claim=(claim or "").strip(),
        context_chunks=_stringify(context_chunks),
    )