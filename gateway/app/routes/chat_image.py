"""``POST /chat/image`` — multipart homework photo, streamed through to the orchestrator."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.core.proxy import proxy_request

router = APIRouter()


@router.post("/chat/image")
async def chat_image(request: Request) -> Response:
    settings = request.app.state.settings
    return await proxy_request(
        request,
        f"{settings.orchestrator_url}/chat/image",
        translate_body=False,
    )
