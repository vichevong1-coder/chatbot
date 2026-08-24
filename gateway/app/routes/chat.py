"""``POST /chat`` — the core loop, proxied to the orchestrator.

THE security-critical behavior of the gateway (.claude/contracts.md section 4):
``student_id`` in the body is OVERWRITTEN with the verified JWT's ``sub``
before proxying. A client-supplied ``student_id`` must never survive, or a
child can impersonate a classmate.

Judgment call: the body is otherwise passed through, not validated against a
dal ChatRequest model — the orchestrator owns that contract and validates it
itself; duplicating the schema here would create a second place to keep in
sync for no security gain (the one field the gateway must control is forced,
not validated). This is also why the gateway deliberately has no dal
dependency.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/chat")
@router.post("/tutor")
async def chat(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.orchestrator_url}/chat",
        body_override={"student_id": request.state.student_id},
    )
