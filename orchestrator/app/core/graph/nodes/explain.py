"""Node 5 — pedagogy_service generates the grade-banded explanation.

Problem context comes from content_service's PUBLIC endpoint, which strips
``correct_answer`` — in Phase 1 the orchestrator must neither see nor forward
the answer to pedagogy (contracts.md §4).

If pedagogy is down the child gets the generic bilingual Tunsay fallback,
never a 500 (claude.md §5 error convention).
"""

from __future__ import annotations

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients, ServiceUnavailable
from app.session_store import cache

DEFAULT_GRADE = 4  # TODO(P2): pull the real grade from the auth profile (auth_client.get_me)

# Authored fallback pair for when pedagogy_service itself is unreachable.
FALLBACK_KHMER = (
    "អូ៎! ទន្សាយកំពុងគិតយឺតបន្តិចហើយ។ សូមសួរម្តងទៀតបន្តិចទៀតណា! 🐰"
)
FALLBACK_ENG = "Oh no! Tunsay is thinking a little slowly. Please ask again in a moment! 🐰"


def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    """Single-language rule (contracts.md §3): requested side filled, other ""."""
    if language == "km":
        return khmer, ""
    return "", eng


def _build_context(problem: dict, language: str, active_step_index: int | None) -> str:
    """Compact context string: title + statement + current step question.

    Built exclusively from the public problem shape — there is no
    ``correct_answer`` in it to leak.
    """
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


async def explain(state: GraphState, clients: ServiceClients) -> dict:
    language = state.get("language", "km")
    mode = state.get("mode", "student")
    grade = DEFAULT_GRADE
    context: str | None = None

    problem_id = state.get("problem_id")
    step_index = state.get("active_step_index")
    misconception_code = state.get("misconception_code")

    if problem_id:
        try:
            problem = await clients.content.get_problem(problem_id)
        except ServiceUnavailable:
            problem = None  # content down/unknown → explain without context
        if problem:
            grade = int(problem.get("grade") or DEFAULT_GRADE)
            context = _build_context(problem, language, step_index)
    else:
        student_id = state.get("student_id")
        if student_id and student_id != "anonymous":
            try:
                prof = await clients.profile.get_profile(student_id)
                if prof and prof.get("grade"):
                    grade = int(prof["grade"])
            except ServiceUnavailable:
                pass

    # Check explanation cache for identical problem step queries
    cache_key = cache.hash_explanation_key(
        problem_id=problem_id,
        step_index=step_index,
        grade=grade,
        misconception_code=misconception_code,
        language=language,
        mode=mode,
    )
    if problem_id:
        cached = await cache.get(cache_key)
        if cached:
            return {
                "intent": "explain",
                "text_khmer": cached.get("text_khmer", ""),
                "text_eng": cached.get("text_eng", ""),
                "is_parent_help": mode == "parent",
            }

    # Append transcript summary if it gets long (to prevent context window overflow)
    transcript = state.get("transcript") or []
    if transcript:
        from app.session_store.summarizer import summarize_transcript
        _, summary = summarize_transcript(transcript, language)
        if summary:
            context = f"{summary}\n\n{context}" if context else summary

    # Append misconception code to context so the pedagogy service can tailor the prompt
    if misconception_code:
        suffix = f"Student Misconception Code: {misconception_code}"
        context = f"{context}\n\n{suffix}" if context else suffix

    try:
        result = await clients.pedagogy.explain(
            prompt=state.get("prompt", ""),
            grade=grade,
            language=language,
            mode=mode,
            context=context,
            misconception_code=misconception_code,
        )
        text_khmer = result.get("text_khmer", "")
        text_eng = result.get("text_eng", "")
        if problem_id and (text_khmer or text_eng):
            await cache.set(cache_key, text_khmer=text_khmer, text_eng=text_eng)
    except ServiceUnavailable:
        text_khmer, text_eng = _pick(FALLBACK_KHMER, FALLBACK_ENG, language)

    return {
        "intent": "explain",
        "text_khmer": text_khmer,
        "text_eng": text_eng,
        "is_parent_help": mode == "parent",
    }
