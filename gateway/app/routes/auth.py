"""Auth proxy routes.

``/auth/register`` and ``/auth/login`` are PUBLIC (they are how you get a
token); ``/auth/me`` is protected by auth_verify and forwards the
Authorization header so auth_service can decode it itself.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/auth/register")
async def register(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(request, f"{settings.auth_service_url}/register")


@router.post("/auth/login")
async def login(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(request, f"{settings.auth_service_url}/login")


@router.get("/auth/me")
async def me(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(request, f"{settings.auth_service_url}/me")
