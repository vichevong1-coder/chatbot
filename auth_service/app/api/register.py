"""POST /register — both entry flows from LoginView.tsx.

- school-code flow: the code must exist in ``schools``; it resolves grade/class.
- public-signup flow: explicit grade (the dal schema enforces one or the other).

No password, no email, no role — every account is a student
(.claude/contracts.md section 4). Registering auto-logs-in: returns a TokenResponse.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from dal.schemas.user import RegisterRequest, TokenResponse, UserProfile

from app.api import errors
from app.api.deps import get_repository
from app.core import jwt_handler, password_hashing
from app.infrastructure.repository import AuthRepository, DuplicateStudentError

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    response_model_by_alias=False,  # snake_case on the wire; the gateway camelCases
    status_code=201,
)
async def register(
    body: RegisterRequest,
    repo: AuthRepository = Depends(get_repository),
) -> TokenResponse:
    grade = body.grade
    class_name = body.class_name

    if body.school_code:
        school = await repo.get_school(body.school_code)
        if school is None:
            raise errors.unknown_school_code(body.school_code)
        # The code resolves grade/class; an explicit request value still wins.
        grade = grade if grade is not None else school.grade
        class_name = class_name if class_name is not None else school.class_name

    if grade is None:
        raise errors.grade_unresolved()

    pin_hash = password_hashing.hash_pin(body.pin) if body.pin else None

    try:
        user = await repo.create_user(
            student_name=body.student_name,
            school_code=body.school_code,
            class_name=class_name,
            grade=grade,
            parent_contact=body.parent_contact,
            pin_hash=pin_hash,
            language=body.language.value,
        )
    except DuplicateStudentError:
        raise errors.duplicate_student()

    token, expires_in = jwt_handler.issue_token(
        user_id=user.id,
        student_name=user.student_name,
        school_code=user.school_code,
        grade=grade,
    )
    profile = UserProfile(
        name=user.student_name,
        grade=grade,
        language=body.language,
        completed_problems_count=0,  # student_profile_service owns these later
        stars_earned=0,
    )
    return TokenResponse(access_token=token, expires_in=expires_in, profile=profile)
