"""GET /me — decode the Bearer token and return the child's profile.

Grade/language come from the DB row, not the token, so a profile edit takes effect
without reissuing tokens. ``completed_problems_count`` / ``stars_earned`` default to 0
here — student_profile_service owns them (P2.3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from dal.schemas.user import UserProfile

from app.api import errors
from app.api.deps import get_repository
from app.core.jwt_handler import TokenError, decode_token
from app.infrastructure.repository import AuthRepository

router = APIRouter()


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise errors.invalid_token()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise errors.invalid_token()
    return token.strip()


@router.get(
    "/me",
    response_model=UserProfile,
    response_model_by_alias=False,  # snake_case on the wire; the gateway camelCases
)
async def me(
    authorization: str | None = Header(default=None),
    repo: AuthRepository = Depends(get_repository),
) -> UserProfile:
    token = _bearer_token(authorization)
    try:
        claims = decode_token(token)
    except TokenError:
        raise errors.invalid_token()

    user = await repo.get_user_by_id(str(claims.get("sub", "")))
    if user is None or user.grade is None:
        raise errors.invalid_token()

    return UserProfile(
        name=user.student_name,
        grade=user.grade,
        language=user.language,
        completed_problems_count=0,  # student_profile_service owns these later
        stars_earned=0,
    )
