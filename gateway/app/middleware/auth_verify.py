"""JWT verification middleware.

Decodes the HS256 token auth_service issued (claims include ``sub`` = user id;
there is NO role claim — every account is a student, .claude/contracts.md
section 4) and stashes the verified ``student_id`` on ``request.state`` for
the rate limiter and the /chat route, which overwrites any client-supplied
``student_id`` with it.

Public paths (/auth/register, /auth/login, /health) bypass verification.
Paths that match no protected prefix fall through to the router, which 404s
them — this is how ``/admin/*`` returns 404 rather than 401: there is no
admin surface on the gateway at all, so there is nothing to guard.
"""

from __future__ import annotations

import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import errors
from app.core.settings import Settings

PUBLIC_PATHS = frozenset({"/auth/register", "/auth/login", "/health"})
PROTECTED_PREFIXES = ("/auth/me", "/chat", "/problems", "/answers", "/hints", "/profile")


class AuthVerifyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if (
            request.method == "OPTIONS"  # preflights are CORS middleware's job
            or path in PUBLIC_PATHS
            or not path.startswith(PROTECTED_PREFIXES)
        ):
            return await call_next(request)

        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return errors.unauthorized_response()

        try:
            claims = jwt.decode(
                token.strip(),
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
            )
        except jwt.InvalidTokenError:
            # Covers expired, tampered, malformed — all one bilingual 401.
            return errors.unauthorized_response()

        student_id = claims.get("sub")
        if not student_id:
            return errors.unauthorized_response()

        request.state.student_id = str(student_id)
        request.state.jwt_claims = claims
        return await call_next(request)
