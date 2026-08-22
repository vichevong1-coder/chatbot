"""Node: recommend_next selects the next homework problem for a student.

Queries student_profile_service for mastery levels and completed problems,
queries content_service for available problems in the student's grade/band,
and recommends an uncompleted problem or a problem for the lowest-mastery skill.

Handles downstream ServiceUnavailable gracefully without failing the chat turn.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients, ServiceUnavailable

DEFAULT_GRADE = 4

# Coarse skill categories mapping
PROBLEM_SKILL_MAP = {
    "math-g3-perimeter": "perimeter",
    "math-g4-apples": "multiplication",
    "math-g4-fractions": "fractions",
    "science-g4-water": "matter",
    "english-g3-continuous": "continuous_tense",
    "english-g4-grammar": "grammar",
    "science-g5-plants": "plants",
}


def resolve_skill(problem_id: str) -> str:
    return PROBLEM_SKILL_MAP.get(problem_id, "general")


def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    if language == "km":
        return khmer, ""
    return "", eng


async def recommend_next(state: GraphState, clients: ServiceClients) -> dict[str, Any]:
    """Determine the next suggested problem for the student."""
    language = state.get("language", "km")
    student_id = state.get("student_id")
    current_problem_id = state.get("problem_id")

    grade = DEFAULT_GRADE
    profile: dict[str, Any] | None = None

    # 1. Fetch student profile if student_id is set
    if student_id and student_id != "anonymous":
        try:
            profile = await clients.profile.get_profile(student_id)
            if profile and profile.get("grade"):
                grade = int(profile["grade"])
        except ServiceUnavailable:
            profile = None
        except Exception:
            profile = None

    # If grade not from profile, check current problem grade
    if current_problem_id:
        try:
            cur_prob = await clients.content.get_problem(current_problem_id)
            if cur_prob and cur_prob.get("grade"):
                grade = int(cur_prob["grade"])
        except ServiceUnavailable:
            pass
        except Exception:
            pass

    # 2. Query available problems from content_service
    problems: list[dict[str, Any]] = []
    try:
        problems = await clients.content.list_problems(grade=grade)
    except ServiceUnavailable:
        problems = []
    except Exception:
        problems = []

    # If no problems found for that specific grade, try listing without grade filter
    if not problems:
        try:
            problems = await clients.content.list_problems()
        except (ServiceUnavailable, Exception):
            problems = []

    # 3. Select best recommendation
    suggested_problem_id: str | None = None
    suggested_problem: dict[str, Any] | None = None

    if problems:
        # Exclude currently active problem if there are other candidates
        candidates = [p for p in problems if p.get("id") != current_problem_id]
        if not candidates:
            candidates = problems

        # Parse completed problems from profile
        completed_set: set[str] = set()
        if profile:
            raw_completed = profile.get("completed_problems") or []
            if isinstance(raw_completed, list):
                completed_set = {
                    p if isinstance(p, str) else p.get("id", "")
                    for p in raw_completed
                }

        # Filter uncompleted if any exist
        uncompleted = [p for p in candidates if p.get("id") not in completed_set]
        pool = uncompleted if uncompleted else candidates

        # Check mastery levels from profile: dict[str, float]
        mastery_levels: dict[str, float] = {}
        if profile and isinstance(profile.get("mastery_levels"), dict):
            mastery_levels = profile["mastery_levels"]

        # Sort by mastery score for the problem's skill (lowest mastery first)
        def score_problem(prob: dict[str, Any]) -> tuple[float, str]:
            prob_id = prob.get("id", "")
            skill = resolve_skill(prob_id)
            # Default mastery score is 0.0 (unmastered/unattempted)
            mastery = float(mastery_levels.get(skill, 0.0))
            return (mastery, prob_id)

        pool.sort(key=score_problem)
        suggested_problem = pool[0]
        suggested_problem_id = suggested_problem.get("id")

    # 4. Generate user-facing text
    if suggested_problem:
        title_km = suggested_problem.get("title_khmer") or suggested_problem.get("title_eng") or ""
        title_en = suggested_problem.get("title_eng") or suggested_problem.get("title_khmer") or ""
        txt_km = f"ទន្សាយសូមណែនាំលំហាត់បន្ទាប់៖ {title_km} 🐰"
        txt_en = f"Tunsay recommends practicing this next problem: {title_en} 🐰"
    else:
        txt_km = "ទន្សាយមិនទាន់អាចរកឃើញលំហាត់ណែនាំនៅពេលនេះទេ។ សូមសាកល្បងម្ដងទៀត! 🐰"
        txt_en = "Tunsay couldn't find any problem recommendations right now. Please try again! 🐰"

    text_khmer, text_eng = _pick(txt_km, txt_en, language)

    mode = state.get("mode", "student")
    return {
        "intent": state.get("intent") or "recommend_next",
        "suggested_next": suggested_problem_id,
        "text_khmer": text_khmer,
        "text_eng": text_eng,
        "is_parent_help": mode == "parent",
    }
