from __future__ import annotations

import json
import asyncio
from typing import Any, Dict, List, Optional

from app.core.llm_client import LLMClient
from app.prompts.reasoning_prompts import build_planner_prompt
from .query_classifier import _classify_query_deterministic
from .query_decomposer import _decompose_query_deterministic
from app.schemas.llm_config import LLMConfig
from app.core.provider_config import resolve_llm_config 


def _generate_plan_steps_deterministic(goal: str, context: Optional[str] = None) -> List[Dict[str, Any]]:
    label = _classify_query_deterministic(goal, context=context)["label"]
    steps: List[Dict[str, Any]] = []

    steps.append({
        "step": 1,
        "action": "classify",
        "objective": f"Determine reasoning mode for query type: {label}.",
        "stop_when": "A routing label has been assigned.",
    })

    current_step = 2

    if label == "GENERAL_CHAT":
        steps.append({
            "step": current_step,
            "action": "respond",
            "objective": "Return a concise conversational reply without retrieval.",
            "stop_when": "A direct conversational response is ready.",
        })
        return steps

    if label == "OUT_OF_SCOPE":
        steps.append({
            "step": current_step,
            "action": "refuse_or_redirect",
            "objective": "Explain that the question is outside the grounded study scope.",
            "stop_when": "A safe scoped response has been prepared.",
        })
        return steps

    if label == "DECOMPOSITION_REQUIRED":
        sub_questions = _decompose_query_deterministic(goal)
        steps.append({
            "step": current_step,
            "action": "decompose",
            "objective": f"Split the question into {len(sub_questions)} focused sub-questions.",
            "stop_when": "All retrievable sub-questions are listed.",
        })
        current_step += 1
        steps.append({
            "step": current_step,
            "action": "retrieve",
            "objective": "Retrieve evidence for each sub-question.",
            "stop_when": "Evidence has been collected for each sub-question or marked insufficient.",
        })
        current_step += 1
    else:
        steps.append({
            "step": current_step,
            "action": "retrieve",
            "objective": "Retrieve the most relevant evidence for the question.",
            "stop_when": "Top supporting chunks have been collected.",
        })
        current_step += 1

    steps.append({
        "step": current_step,
        "action": "synthesize",
        "objective": "Build a grounded answer using only retrieved evidence.",
        "stop_when": "Every substantive statement in the draft answer is evidence-backed.",
    })
    current_step += 1

    steps.append({
        "step": current_step,
        "action": "verify",
        "objective": "Check for unsupported claims and insufficiency.",
        "stop_when": "The final answer is either supported or explicitly marked insufficient.",
    })

    return steps


async def generate_plan_steps_async(
    goal: str, 
    context: Optional[str] = None, 
    user_config: Optional[LLMConfig] = None
) -> List[Dict[str, Any]]:
    """Try LLM first for intelligent planning."""
    
    resolved = resolve_llm_config(user_config)
    client = LLMClient(resolved)
    
    prompt = build_planner_prompt(goal=goal, context=context)
    messages = [
        {"role": "system", "content": "You are a helpful assistant that outputs strictly in JSON."},
        {"role": "user", "content": prompt}
    ]

    llm_response = await client.chat(messages=messages, temperature=0.0, json_mode=True)
    
    if llm_response:
        try:
            result = json.loads(llm_response)
            if "steps" in result:
                return result["steps"]
        except json.JSONDecodeError:
            pass

    return _generate_plan_steps_deterministic(goal, context)


def generate_plan_steps(
    goal: str, 
    context: Optional[str] = None, 
    user_config: Optional[LLMConfig] = None
):
    """Synchronous wrapper for backward compatibility."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(generate_plan_steps_async(goal, context, user_config))
    else:
        return asyncio.run(generate_plan_steps_async(goal, context, user_config))


def render_plan(plan_steps: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for item in plan_steps:
        step = item.get("step", "?")
        action = item.get("action", "unknown")
        objective = item.get("objective", "")
        stop_when = item.get("stop_when", "")
        lines.append(f"Step {step} [{action}]: {objective} Stop when: {stop_when}")
    return " ".join(lines)


def generate_plan(goal: str, context: Optional[str] = None, user_config: Optional[LLMConfig] = None) -> str:
    result = generate_plan_steps(goal=goal, context=context, user_config=user_config)
    if asyncio.isfuture(result) or asyncio.istask(result):
        # Fallback to sync execution immediately if blocked by task
        return render_plan(_generate_plan_steps_deterministic(goal, context))
    return render_plan(result)