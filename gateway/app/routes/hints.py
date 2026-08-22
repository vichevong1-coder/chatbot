"""``POST /hints`` — AI-generated hint proxy, routed to the orchestrator.

Like /chat, student_id in the body is overwritten with the verified JWT's sub.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/hints")
async def hints(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.orchestrator_url}/hints",
        body_override={"student_id": request.state.student_id},
    )
