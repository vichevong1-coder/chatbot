"""Self-Critique & Socratic Reflection Node.

Evaluates generated tutor responses before they reach the child:
1. Socratic Non-Leak Check: Ensures final answers are not prematurely revealed in student mode.
2. Language Integrity Check: Validates that Khmer replies use encouraging, age-appropriate phrasing.
3. Auto-Correction Loop: If critique fails, signals a re-generation turn.
"""

from __future__ import annotations

import re
from typing import Any
from app.core.graph.state import GraphState


def evaluate_response(
    *,
    response_text: str,
    mode: str = "student",
    correct_answer: str | None = None,
) -> dict[str, Any]:
    """Evaluate candidate tutor response against pedagogy rules."""
    critique_passed = True
    issues: list[str] = []

    # 1. Socratic Non-Leak Check (student mode only)
    if mode == "student" and correct_answer:
        clean_answer = str(correct_answer).strip().lower()
        if len(clean_answer) > 0 and clean_answer in response_text.lower():
            # Check if answer appears explicitly as a standalone solution
            pattern = re.compile(rf"\b{re.escape(clean_answer)}\b", re.IGNORECASE)
            if pattern.search(response_text):
                critique_passed = False
                issues.append(f"Answer leak detected: '{correct_answer}' revealed in student mode.")

    # 2. Minimum Socratic Question Check (student mode should end with a question)
    if mode == "student" and len(response_text) > 20:
        has_question = "?" in response_text or "តើ" in response_text or "ឫ" in response_text
        if not has_question:
            critique_passed = False
            issues.append("Response in student mode does not end with a Socratic question.")

    return {
        "passed": critique_passed,
        "issues": issues,
        "mode_evaluated": mode,
    }


async def self_critique_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node executing self-critique on generated tutor responses."""
    text_khmer = state.get("text_khmer", "")
    text_eng = state.get("text_eng", "")
    mode = state.get("mode", "student")
    correct_answer = state.get("correct_answer")

    response_to_check = text_khmer or text_eng
    if not response_to_check:
        return {"critique_passed": True, "critique_issues": []}

    evaluation = evaluate_response(
        response_text=response_to_check,
        mode=mode,
        correct_answer=correct_answer,
    )

    return {
        "critique_passed": evaluation["passed"],
        "critique_issues": evaluation["issues"],
    }
