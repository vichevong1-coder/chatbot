"""Gateway app factory — the single public surface, port 8000.

Everything the browser can reach goes through here (.claude/contracts.md
section 4). There is deliberately NO /admin/* route: content editing never
passes through the gateway, and /admin/anything 404s.

Middleware order (outermost first): cors -> auth_verify -> rate_limit -> route.
Starlette runs the LAST-added middleware first, so they are added in reverse.

``create_app`` takes an injectable httpx client, settings, and rate limiter so
tests can mock every upstream and drive the clock.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request

from app.core.settings import Settings
from app.middleware.auth_verify import AuthVerifyMiddleware
from app.middleware.cors import add_cors
from app.middleware.rate_limit import RateLimiter, RateLimitMiddleware
from app.routes import auth, chat, chat_audio, problems, answers

SERVICE_NAME = "gateway"

_HEALTH_TIMEOUT_SECONDS = 2.0


def create_app(
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    owns_client = http_client is None

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        yield
        if owns_client:
            await application.state.http_client.aclose()

    app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)
    app.state.settings = settings
    app.state.http_client = http_client or httpx.AsyncClient(timeout=30.0)

    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(chat_audio.router)
    app.include_router(problems.router)
    app.include_router(answers.router)

    @app.get("/health")
    async def health(request: Request) -> dict[str, str]:
        """Gateway is ok if it is answering; downstream checks are best-effort.

        Never fails, even with every service down — a health endpoint that
        500s when its dependencies are down is useless for diagnosis.
        """
        client: httpx.AsyncClient = request.app.state.http_client
        targets = {
            "auth_service": settings.auth_service_url,
            "orchestrator": settings.orchestrator_url,
            "content_service": settings.content_service_url,
        }

        async def probe(base_url: str) -> str:
            try:
                response = await asyncio.wait_for(
                    client.get(f"{base_url}/health", timeout=_HEALTH_TIMEOUT_SECONDS),
                    timeout=_HEALTH_TIMEOUT_SECONDS + 0.5,
                )
                return "ok" if response.status_code == 200 else "down"
            except Exception:
                return "down"

        statuses = await asyncio.gather(*(probe(url) for url in targets.values()))
        return {"status": "ok", "service": SERVICE_NAME, **dict(zip(targets, statuses))}

    # Reverse order of execution: last added runs first.
    app.add_middleware(
        RateLimitMiddleware,
        limiter=rate_limiter
        or RateLimiter(
            limit=settings.chat_rate_limit,
            window_seconds=settings.chat_rate_window_seconds,
        ),
    )
    app.add_middleware(AuthVerifyMiddleware, settings=settings)
    add_cors(app, settings)  # outermost

    return app


app = create_app()
