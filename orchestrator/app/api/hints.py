"""POST /hints — AI-generated progressive hint router."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from dal.schemas import HintRequest, HintResponse
from app.utils.logging import get_logger, log_event
from app.infrastructure.service_clients import ServiceUnavailable

router = APIRouter()
logger = get_logger("orchestrator")

DEFAULT_GRADE = 4

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

FALLBACK_KHMER = "សូមមើលសំណួរម្តងទៀតដោយប្រុងប្រយ័ត្ន ឬសួរគ្រូបង្រៀនរបស់អ្នកសម្រាប់ជំនួយបន្ថែម! 🐰"
FALLBACK_ENG = "Please read the question carefully again or ask your teacher for extra help! 🐰"


def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    if language == "km":
        return khmer, ""
    return "", eng


def _build_step_context(problem: dict, step: dict, language: str) -> str:
    is_khmer = language == "km"

    def bi(khmer: str | None, eng: str | None) -> str:
        return (khmer or eng or "") if is_khmer else (eng or khmer or "")

    parts = [
        bi(problem.get("title_khmer"), problem.get("title_eng")),
        bi(problem.get("problem_statement_khmer"), problem.get("problem_statement_eng")),
    ]
    step_question = bi(step.get("question_khmer"), step.get("question_eng"))
    if step_question:
        label = "ជំហានបច្ចុប្បន្ន" if is_khmer else "Current step"
        parts.append(f"{label}: {step_question}")

    return "\n".join(part for part in parts if part)


@router.post("/hints", response_model=HintResponse, response_model_by_alias=False)
async def generate_hint(request: Request, body: HintRequest) -> HintResponse:
    started = time.perf_counter()
    clients = request.app.state.clients
    language = body.language.value

    # 1. Fetch problem from content service
    try:
        problem = await clients.content.get_problem(body.problem_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch problem from content service: {str(exc)}",
        )

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem {body.problem_id} not found")

    steps = problem.get("steps") or []
    target_step = None
    for step in steps:
        if step.get("id") == body.step_id:
            target_step = step
            break

    if not target_step:
        raise HTTPException(
            status_code=404,
            detail=f"Step {body.step_id} not found in problem {body.problem_id}",
        )

    grade = int(problem.get("grade") or DEFAULT_GRADE)
    hint_instruction = HINT_INSTRUCTIONS.get(body.hint_level, HINT_INSTRUCTIONS[1])
    step_context = _build_step_context(problem, target_step, language)
    full_context = f"{hint_instruction}\n\n{step_context}"

    prompt_label = (
        f"ផ្តល់តម្រុយកម្រិតទី {body.hint_level} សម្រាប់ជំហាននេះ"
        if language == "km"
        else f"Give hint level {body.hint_level} for this step"
    )

    try:
        result = await clients.pedagogy.explain(
            prompt=prompt_label,
            grade=grade,
            language=language,
            mode="student",
            context=full_context,
        )
        hint_khmer = result.get("text_khmer", "")
        hint_eng = result.get("text_eng", "")
    except ServiceUnavailable:
        hint_khmer, hint_eng = _pick(FALLBACK_KHMER, FALLBACK_ENG, language)

    response = HintResponse(
        hint_khmer=hint_khmer,
        hint_eng=hint_eng,
        hint_level=body.hint_level,
    )

    log_event(
        logger,
        "hint_generated",
        student_id=body.student_id or "anonymous",
        session_id=body.session_id,
        intent="hint",
        duration_ms=(time.perf_counter() - started) * 1000,
    )

    return response
