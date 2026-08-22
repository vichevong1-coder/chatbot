"""Node 7 — hint node generates progressive Socratic hints via pedagogy_service.

Escalates hint levels 1 -> 2 -> 3:
- Level 1: Small nudge, guiding question only.
- Level 2: Specific hint mentioning the relevant concept/operation.
- Level 3: Detailed hint with a similar worked example using different numbers.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients, ServiceUnavailable

DEFAULT_GRADE = 4

FALLBACK_KHMER = "អូ៎! ទន្សាយកំពុងគិតយឺតបន្តិចហើយ។ សូមសួរម្តងទៀតបន្តិចទៀតណា! 🐰"
FALLBACK_ENG = "Oh no! Tunsay is thinking a little slowly. Please ask again in a moment! 🐰"

HINT_INSTRUCTIONS = {
    1: (
        "HINT LEVEL 1 (Gentle Nudge): Give only a tiny, gentle nudge or ask one guiding question. "
        "Do NOT explain the method or reveal the answer."
    ),
    2: (
        "HINT LEVEL 2 (Targeted Clue): Provide a more specific hint. Mention the relevant concept "
        "or arithmetic operation to use, but do NOT calculate the answer."
    ),
    3: (
        "HINT LEVEL 3 (Worked Similar Example): Provide a very detailed hint with a worked similar example "
        "using DIFFERENT numbers. Still do NOT give the actual answer to the student's problem."
    ),
}


def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    if language == "km":
        return khmer, ""
    return "", eng


def _build_context(problem: dict, language: str, active_step_index: int | None) -> str:
    is_khmer = language == "km"

    def bi(khmer: str | None, eng: str | None) -> str:
        return (khmer or eng or "") if is_khmer else (eng or khmer or "")

    parts = [
        bi(problem.get("title_khmer"), problem.get("title_eng")),
        bi(problem.get("problem_statement_khmer"), problem.get("problem_statement_eng")),
    ]
    steps = problem.get("steps") or []
    index = active_step_index if active_step_index is not None else 0
    if 0 <= index < len(steps):
        step = steps[index]
        question = bi(step.get("question_khmer"), step.get("question_eng"))
        if question:
            label = "ជំហានបច្ចុប្បន្ន" if is_khmer else "Current step"
            parts.append(f"{label}: {question}")
    return "\n".join(part for part in parts if part)


async def hint(state: GraphState, clients: ServiceClients) -> dict[str, Any]:
    language = state.get("language", "km")
    mode = state.get("mode", "student")
    current_level = state.get("hint_level", 0)
    next_level = min(max(current_level + 1, 1), 3)

    grade = DEFAULT_GRADE
    context: str | None = None

    problem_id = state.get("problem_id")
    if problem_id:
        try:
            problem = await clients.content.get_problem(problem_id)
        except ServiceUnavailable:
            problem = None
        if problem:
            grade = int(problem.get("grade") or DEFAULT_GRADE)
            context = _build_context(problem, language, state.get("active_step_index"))
    else:
        student_id = state.get("student_id")
        if student_id and student_id != "anonymous":
            try:
                prof = await clients.profile.get_profile(student_id)
                if prof and prof.get("grade"):
                    grade = int(prof["grade"])
            except ServiceUnavailable:
                pass

    # Prepend hint level instruction
    hint_instruction = HINT_INSTRUCTIONS.get(next_level, HINT_INSTRUCTIONS[1])
    context = f"{hint_instruction}\n\n{context}" if context else hint_instruction

    transcript = state.get("transcript") or []
    if transcript:
        from app.session_store.summarizer import summarize_transcript
        _, summary = summarize_transcript(transcript, language)
        if summary:
            context = f"{summary}\n\n{context}"

    try:
        result = await clients.pedagogy.explain(
            prompt=state.get("prompt", ""),
            grade=grade,
            language=language,
            mode=mode,
            context=context,
        )
        text_khmer = result.get("text_khmer", "")
        text_eng = result.get("text_eng", "")
    except ServiceUnavailable:
        text_khmer, text_eng = _pick(FALLBACK_KHMER, FALLBACK_ENG, language)

    return {
        "intent": "hint",
        "hint_level": next_level,
        "text_khmer": text_khmer,
        "text_eng": text_eng,
        "is_parent_help": mode == "parent",
    }
