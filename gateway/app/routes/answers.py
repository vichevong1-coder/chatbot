"""``POST /answers`` — answer checking proxy, routed to the orchestrator.

Like /chat, student_id in the body is overwritten with the verified JWT's sub.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/answers")
async def answers(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.orchestrator_url}/answers",
        body_override={"student_id": request.state.student_id},
    )
