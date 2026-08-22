"""Profile proxy routes — student progress, hints, and attempts routed to student_profile_service.

All profile routes are protected by AuthVerifyMiddleware: student_id is verified from the JWT.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core import errors
from app.core.proxy import proxy_request

router = APIRouter()


@router.get("/profile/{student_id}")
async def get_profile(student_id: str, request: Request) -> Response:
    settings = request.app.state.settings
    # Overwrite/inject verified student_id from JWT sub to prevent spoofing
    verified_id = getattr(request.state, "student_id", None)
    if not verified_id:
        return errors.unauthorized_response()
    return await proxy_request(
        request,
        f"{settings.student_profile_service_url}/profile/{verified_id}",
    )


@router.get("/profile")
async def get_my_profile(request: Request) -> Response:
    settings = request.app.state.settings
    verified_id = getattr(request.state, "student_id", None)
    if not verified_id:
        return errors.unauthorized_response()
    return await proxy_request(
        request,
        f"{settings.student_profile_service_url}/profile/{verified_id}",
    )


@router.post("/profile/hints")
async def profile_hints(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.student_profile_service_url}/profile/hints",
        body_override={"student_id": request.state.student_id},
    )


@router.post("/profile/attempts")
async def profile_attempts(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.student_profile_service_url}/profile/attempts",
        body_override={"student_id": request.state.student_id},
    )
