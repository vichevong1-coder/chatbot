"""POST /login — the returning-login flow.

Identity is (school_code, student_name); either may be given alone, and the match must
be unambiguous. PIN semantics (.claude/contracts.md section 4):

- account with **no** pin_hash + no PIN given -> OK (shared classroom device; the school
  code is the real credential). A PIN supplied anyway is ignored.
- account **with** pin_hash -> the correct PIN is required; wrong or missing -> 401.

Wrong PINs feed the per-identity throttle; a locked identity gets a structured 429
before any PIN check happens.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from dal.schemas.user import LoginRequest, TokenResponse, UserProfile

from app.api import errors
from app.api.deps import get_repository, get_throttle
from app.core import jwt_handler, password_hashing
from app.core.throttle import AttemptThrottle
from app.infrastructure.repository import AuthRepository

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    response_model_by_alias=False,  # snake_case on the wire; the gateway camelCases
)
async def login(
    body: LoginRequest,
    repo: AuthRepository = Depends(get_repository),
    throttle: AttemptThrottle = Depends(get_throttle),
) -> TokenResponse:
    key = (body.school_code or "", body.student_name or "")
    retry_after = throttle.retry_after(key)
    if retry_after is not None:
        raise errors.too_many_attempts(retry_after)

    users = await repo.find_users(
        student_name=body.student_name, school_code=body.school_code
    )
    if len(users) != 1:
        # Zero matches and ambiguous matches look identical to the caller: never
        # reveal whether a name exists.
        raise errors.invalid_credentials()
    user = users[0]

    if user.pin_hash:
        if not body.pin:
            raise errors.invalid_credentials()
        if not password_hashing.verify_pin(body.pin, user.pin_hash):
            throttle.record_failure(key)
            raise errors.invalid_credentials()

    throttle.record_success(key)

    if user.grade is None:
        raise errors.grade_unresolved()

    token, expires_in = jwt_handler.issue_token(
        user_id=user.id,
        student_name=user.student_name,
        school_code=user.school_code,
        grade=user.grade,
    )
    profile = UserProfile(
        name=user.student_name,
        grade=user.grade,
        language=user.language,
        completed_problems_count=0,  # student_profile_service owns these later
        stars_earned=0,
    )
    return TokenResponse(access_token=token, expires_in=expires_in, profile=profile)
