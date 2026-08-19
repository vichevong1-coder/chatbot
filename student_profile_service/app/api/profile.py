"""API routes for student profile and progress persistence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dal.models.problem import Problem
from dal.models.step import Step
from app.api.deps import get_repository
from app.api.schemas import (
    AnswerAttemptRequest,
    HintUsageRequest,
    HintUsageResponse,
    StudentProfileResponse,
)
from app.core.mastery_model import calculate_new_mastery, resolve_skill
from app.infrastructure.progress_repository import ProgressRepository

router = APIRouter(tags=["profile"])


@router.get("/profile/{student_id}", response_model=StudentProfileResponse)
async def get_profile(
    student_id: str,
    repo: ProgressRepository = Depends(get_repository),
) -> StudentProfileResponse:
    """Fetch student profile including stars, completed problems, and masteries."""
    profile = await repo.get_or_create_profile(student_id)
    masteries = await repo.get_skill_masteries(student_id)

    mastery_levels = {m.skill: m.mastery for m in masteries}

    return StudentProfileResponse(
        student_id=profile.student_id,
        stars=profile.stars_earned,
        completed_problems_count=profile.completed_problems_count,
        mastery_levels=mastery_levels,
    )


@router.post("/profile/attempts", status_code=201)
async def record_attempt(
    body: AnswerAttemptRequest,
    repo: ProgressRepository = Depends(get_repository),
) -> dict[str, str]:
    """Log a student attempt on a problem step, updating stars and skill mastery."""
    # Resolve problem and step metadata
    async with repo._factory() as session:
        problem = await session.get(Problem, body.problem_id)
        step = await session.get(Step, (body.step_id, body.problem_id))

    if problem:
        subject = problem.subject
        grade = problem.grade
    else:
        subject = "math"
        grade = 4

    skill = resolve_skill(body.problem_id)

    # 1. Update skill mastery level
    mastery_record = await repo.get_or_create_mastery(
        student_id=body.student_id,
        subject=subject,
        grade=grade,
        skill=skill,
    )
    new_mastery = calculate_new_mastery(mastery_record.mastery, body.is_correct)
    await repo.update_mastery(
        mastery_record.id,
        mastery=new_mastery,
        is_correct=body.is_correct,
    )

    # 2. Update Student Profile stars and completed count
    if body.is_correct:
        # Reward 2 stars for correct step answer
        await repo.add_stars(body.student_id, 2)

        # If this is the final step, increment completed problems count
        if step and step.step_number == step.total_steps:
            await repo.increment_completed_problems(body.student_id)

    # 3. Log attempt event
    attempt_count = await repo.get_step_attempt_count(
        student_id=body.student_id,
        problem_id=body.problem_id,
        step_id=body.step_id,
    )
    attempt_number = attempt_count + 1

    await repo.record_attempt(
        student_id=body.student_id,
        session_id=body.session_id,
        problem_id=body.problem_id,
        step_id=body.step_id,
        student_answer=body.student_answer or "submitted answer",
        is_correct=body.is_correct,
        misconception_code=body.misconception_code,
        hint_rung_used=body.hint_rung_used,
        attempt_number=attempt_number,
    )

    return {"status": "recorded"}


@router.post("/profile/hints", response_model=HintUsageResponse)
async def use_hint(
    body: HintUsageRequest,
    repo: ProgressRepository = Depends(get_repository),
) -> HintUsageResponse:
    """Log hint usage and deduct stars accordingly."""
    # Deduct stars based on the hint rung number
    await repo.add_stars(body.student_id, -body.rung)

    profile = await repo.get_or_create_profile(body.student_id)

    return HintUsageResponse(
        success=True,
        remaining_stars=profile.stars_earned,
    )
