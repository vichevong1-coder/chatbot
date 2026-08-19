"""Coarse skill categories mapping and mastery calculation model."""

from __future__ import annotations

# Maps problem slugs to coarse skill tags (P2.3)
PROBLEM_SKILL_MAP = {
    "math-g3-perimeter": "perimeter",
    "math-g4-apples": "multiplication",
    "math-g4-fractions": "fractions",
    "english-g3-continuous": "continuous_tense",
    "english-g4-grammar": "grammar",
    "science-g5-plants": "plants",
}

DEFAULT_SKILL = "general"


def resolve_skill(problem_id: str) -> str:
    """Resolve a coarse skill tag from a problem ID."""
    return PROBLEM_SKILL_MAP.get(problem_id, DEFAULT_SKILL)


def calculate_new_mastery(current_mastery: float, is_correct: bool) -> float:
    """Determine the updated skill mastery based on correctness.

    Increases mastery by +0.1 on success, decays by -0.05 on failure, bounded [0.0, 1.0].
    """
    if is_correct:
        return min(1.0, current_mastery + 0.1)
    return max(0.0, current_mastery - 0.05)
