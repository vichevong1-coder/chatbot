"""Problem catalog proxy — content_service, JWT required, query params forwarded.

Stripping ``correct_answer`` is content_service's job at serialization
(.claude/contracts.md section 4); the gateway only translates key case.
Deliberately NOT rate-limited: browsing problems costs no LLM tokens.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.get("/problems")
async def list_problems(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.content_service_url}/problems",
        forward_query=True,
    )


@router.get("/problems/{problem_id}")
async def get_problem(problem_id: str, request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.content_service_url}/problems/{problem_id}",
        forward_query=True,
    )
