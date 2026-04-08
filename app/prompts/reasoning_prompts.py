"""
Prompt templates and helper builders for the Reasoning pipeline.
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


QUERY_CLASSIFIER_PROMPT = dedent(
    """
    You are an expert query classifier for a grounded tutoring assistant.

    Your task:
    - Read the user's query and any available context.
    - Classify the query into exactly one label:
      1. FACTUAL_QA
      2. DECOMPOSITION_REQUIRED
      3. GENERAL_CHAT
      4. OUT_OF_SCOPE

    Classification rules:
    - FACTUAL_QA: a direct question that can likely be answered from retrieval evidence.
    - DECOMPOSITION_REQUIRED: a multi-hop, comparison, why/how, or multi-part question that should be split first.
    - GENERAL_CHAT: greeting, small talk, or non-knowledge-seeking conversational input.
    - OUT_OF_SCOPE: requests that cannot be answered from the knowledge base or violate system scope.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "label": "FACTUAL_QA | DECOMPOSITION_REQUIRED | GENERAL_CHAT | OUT_OF_SCOPE",
        "reason": "brief explanation"
      }}

    User Query:
    {query}

    Available Context / Metadata:
    {context}

    JSON:
    """
).strip()


QUERY_DECOMPOSER_PROMPT = dedent(
    """
    You are an advanced query decomposer for a grounded RAG tutor.

    Your task:
    - Break the original question into atomic sub-questions.
    - Each sub-question should be answerable with one focused retrieval step.
    - Keep the order logical.
    - Do not invent information not implied by the original question.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "sub_questions": [
          "sub-question 1",
          "sub-question 2"
        ]
      }}

    Original Query:
    {query}

    JSON:
    """
).strip()


PLANNER_PROMPT = dedent(
    """
    You are a bounded planner for a grounded tutoring assistant.

    Your task:
    - Create a short, actionable plan to answer the goal.
    - Prefer retrieval-grounded reasoning over speculation.
    - Include stopping conditions.
    - Do not propose unnecessary steps.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "steps": [
          {{
            "step": 1,
            "action": "retrieve | compare | synthesize | verify",
            "objective": "what this step should accomplish",
            "stop_when": "clear stopping condition"
          }}
        ]
      }}

    Goal:
    {goal}

    Available Knowledge / Context:
    {context}

    JSON:
    """
).strip()


SYNTHESIZER_PROMPT = dedent(
    """
    You are an expert answer synthesizer for a grounded tutoring assistant.

    You must follow these rules strictly:
    1. Use only the provided context chunks.
    2. Do not make unsupported claims.
    3. If the evidence is insufficient, say so explicitly.
    4. Keep the answer clear, concise, and logically structured.
    5. Preserve citation markers exactly when the context already contains them.
    6. Do not fabricate citations.

    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "answer": "final grounded answer",
        "used_evidence": [
          {{
            "document_id": "optional",
            "chunk_id": "optional",
            "page": "optional"
          }}
        ],
        "notes": "state insufficiency or ambiguity if needed"
      }}

    User Query:
    {query}

    Context Chunks:
    {context_chunks}

    JSON:
    """
).strip()


def build_query_classifier_prompt(query: str, context: Any = None) -> str:
    return QUERY_CLASSIFIER_PROMPT.format(
        query=(query or "").strip(),
        context=_stringify(context),
    )


def build_query_decomposer_prompt(query: str) -> str:
    return QUERY_DECOMPOSER_PROMPT.format(
        query=(query or "").strip(),
    )


def build_planner_prompt(goal: str, context: Any = None) -> str:
    return PLANNER_PROMPT.format(
        goal=(goal or "").strip(),
        context=_stringify(context),
    )


def build_synthesizer_prompt(query: str, context_chunks: Any) -> str:
    return SYNTHESIZER_PROMPT.format(
        query=(query or "").strip(),
        context_chunks=_stringify(context_chunks),
    )