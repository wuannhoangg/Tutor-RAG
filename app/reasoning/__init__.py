"""
Reasoning module exports.
Provides deterministic reasoning utilities that can run without an LLM client.
"""

from .citation_builder import (
    attach_citation,
    build_citation_payload,
    build_citation_string,
    format_citations_from_chunks,
)
from .planner import generate_plan, generate_plan_steps, render_plan
from .query_classifier import classify_query, classify_query_with_reason
from .query_decomposer import decompose_query
from .synthesizer import synthesize_answer

__all__ = [
    "classify_query",
    "classify_query_with_reason",
    "decompose_query",
    "generate_plan",
    "generate_plan_steps",
    "render_plan",
    "synthesize_answer",
    "build_citation_string",
    "build_citation_payload",
    "format_citations_from_chunks",
    "attach_citation",
]