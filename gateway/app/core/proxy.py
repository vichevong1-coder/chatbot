"""The proxy engine: forward a request upstream, translating JSON key case.

Inbound JSON bodies: camelCase -> snake_case. Outbound JSON bodies:
snake_case -> camelCase. Values are never touched (case_translate.py).
Non-JSON bodies (multipart audio) stream through untranslated.

Upstream connect failures become a structured bilingual 502 — never a stack
trace. Otherwise the upstream's status code and (translated) body pass
through. Request bodies are never logged: this is children's data.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core import errors
from app.core.case_translate import to_camel_keys, to_snake_keys

# Response headers worth forwarding to the browser; everything else
# (hop-by-hop, content-length, upstream server chatter) is dropped.
_FORWARD_RESPONSE_HEADERS = ("retry-after", "www-authenticate")


async def proxy_request(
    request: Request,
    url: str,
    *,
    body_override: Mapping[str, Any] | None = None,
    forward_query: bool = False,
    translate_body: bool = True,
) -> Response:
    """Forward ``request`` to ``url`` and return the (translated) response.

    ``body_override`` merges into the inbound JSON body AFTER translation to
    snake_case — this is how the verified JWT ``sub`` overwrites any
    client-supplied ``student_id`` (.claude/contracts.md section 4). The
    override always wins; if there is no JSON body it becomes the body.
    """
    client: httpx.AsyncClient = request.app.state.http_client

    headers: dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth

    raw = await request.body()
    content_type = request.headers.get("content-type", "")

    json_body: Any = None
    content: bytes | None = None
    if translate_body and content_type.split(";")[0].strip() == "application/json" and raw:
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = None
        if parsed is not None:
            json_body = to_snake_keys(parsed)
            if body_override is not None and isinstance(json_body, dict):
                json_body.update(body_override)
        else:
            content = raw
            headers["Content-Type"] = content_type
    elif raw:
        content = raw
        if content_type:
            headers["Content-Type"] = content_type

    if json_body is None and content is None and body_override is not None:
        json_body = dict(body_override)

    params = dict(request.query_params) if forward_query else None

    try:
        upstream = await client.request(
            request.method,
            url,
            json=json_body,
            content=content,
            headers=headers,
            params=params,
        )
    except httpx.TransportError:
        # Connect refused / timed out / reset. No detail leaks to the child.
        return errors.upstream_unreachable_response()

    return _translate_response(upstream)


def _translate_response(upstream: httpx.Response) -> Response:
    fwd_headers = {
        name: upstream.headers[name]
        for name in _FORWARD_RESPONSE_HEADERS
        if name in upstream.headers
    }
    content_type = upstream.headers.get("content-type", "")
    if content_type.split(";")[0].strip() == "application/json":
        try:
            data = upstream.json()
        except ValueError:
            data = None
        if data is not None:
            return JSONResponse(
                status_code=upstream.status_code,
                content=to_camel_keys(data),
                headers=fwd_headers or None,
            )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=content_type or None,
        headers=fwd_headers or None,
    )
