"""``POST /chat/audio`` — multipart audio, streamed through to the orchestrator.

The multipart body passes through untranslated (case translation is a JSON
concern); the JSON response, when the orchestrator side exists, is camelCased
like every other. Until then a 502/501 from upstream simply passes through —
the gateway's job is only to proxy. Audio content is never logged
(children's data).

Note ``student_id`` cannot be injected into a multipart body the way /chat
does for JSON; the orchestrator must take identity from ``session_id`` /
the forwarded Authorization header when it implements this endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/chat/audio")
async def chat_audio(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.orchestrator_url}/chat/audio",
        translate_body=False,
    )
