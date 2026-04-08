"""
Generate a bounded reasoning plan for answering user queries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .query_classifier import classify_query
from .query_decomposer import decompose_query


def generate_plan_steps(goal: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return structured plan steps.
    """
    label = classify_query(goal, context=context)
    steps: List[Dict[str, Any]] = []

    steps.append(
        {
            "step": 1,
            "action": "classify",
            "objective": f"Determine reasoning mode for query type: {label}.",
            "stop_when": "A routing label has been assigned.",
        }
    )

    current_step = 2

    if label == "GENERAL_CHAT":
        steps.append(
            {
                "step": current_step,
                "action": "respond",
                "objective": "Return a concise conversational reply without retrieval.",
                "stop_when": "A direct conversational response is ready.",
            }
        )
        return steps

    if label == "OUT_OF_SCOPE":
        steps.append(
            {
                "step": current_step,
                "action": "refuse_or_redirect",
                "objective": "Explain that the question is outside the grounded study scope.",
                "stop_when": "A safe scoped response has been prepared.",
            }
        )
        return steps

    if label == "DECOMPOSITION_REQUIRED":
        sub_questions = decompose_query(goal)
        steps.append(
            {
                "step": current_step,
                "action": "decompose",
                "objective": f"Split the question into {len(sub_questions)} focused sub-questions.",
                "stop_when": "All retrievable sub-questions are listed.",
            }
        )
        current_step += 1

        steps.append(
            {
                "step": current_step,
                "action": "retrieve",
                "objective": "Retrieve evidence for each sub-question.",
                "stop_when": "Evidence has been collected for each sub-question or marked insufficient.",
            }
        )
        current_step += 1
    else:
        steps.append(
            {
                "step": current_step,
                "action": "retrieve",
                "objective": "Retrieve the most relevant evidence for the question.",
                "stop_when": "Top supporting chunks have been collected.",
            }
        )
        current_step += 1

    steps.append(
        {
            "step": current_step,
            "action": "synthesize",
            "objective": "Build a grounded answer using only retrieved evidence.",
            "stop_when": "Every substantive statement in the draft answer is evidence-backed.",
        }
    )
    current_step += 1

    steps.append(
        {
            "step": current_step,
            "action": "verify",
            "objective": "Check for unsupported claims and insufficiency.",
            "stop_when": "The final answer is either supported or explicitly marked insufficient.",
        }
    )

    return steps


def render_plan(plan_steps: List[Dict[str, Any]]) -> str:
    """
    Render structured plan steps into a readable text block.
    """
    lines: List[str] = []
    for item in plan_steps:
        step = item.get("step", "?")
        action = item.get("action", "unknown")
        objective = item.get("objective", "")
        stop_when = item.get("stop_when", "")
        lines.append(f"Step {step} [{action}]: {objective} Stop when: {stop_when}")
    return " ".join(lines)


def generate_plan(goal: str, context: Optional[str] = None) -> str:
    """
    Backward-compatible planner returning text.
    """
    return render_plan(generate_plan_steps(goal=goal, context=context))