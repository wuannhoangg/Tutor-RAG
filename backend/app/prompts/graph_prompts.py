"""
Prompt templates for Knowledge Graph extraction.
"""

from __future__ import annotations
from textwrap import dedent

CONCEPT_EXTRACTOR_PROMPT = dedent(
    """
    You are an expert academic knowledge extractor. 
    
    Your task:
    - Read the provided text chunk.
    - Extract the core academic concepts, technical terms, algorithms, or key entities.
    - Keep concepts concise (1-3 words usually).
    - Return a maximum of 5 most important concepts.
    
    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "concepts": ["Concept 1", "Concept 2", "Concept 3"]
      }}
      
    Text to analyze:
    {text}
    
    JSON:
    """
).strip()

def build_concept_extractor_prompt(text: str) -> str:
    return CONCEPT_EXTRACTOR_PROMPT.format(text=(text or "").strip())

CONCEPT_ROUTER_PROMPT = dedent(
    """
    You are an intelligent query router for an academic tutoring system.
    
    Your task:
    - Analyze the user's query.
    - Identify the primary academic concept or topic the user is asking about.
    - Output ONLY the most relevant concept (1-3 words max).
    - If no specific concept is found, return an empty string.
    
    Output rules:
    - Return valid JSON only.
    - Do not use markdown.
    - Use this schema exactly:
      {{
        "target_concept": "Concept Name"
      }}
      
    User Query:
    {query}
    
    JSON:
    """
).strip()

def build_concept_router_prompt(query: str) -> str:
    return CONCEPT_ROUTER_PROMPT.format(query=(query or "").strip())