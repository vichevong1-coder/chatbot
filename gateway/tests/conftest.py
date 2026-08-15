"""Gateway test fixtures.

Upstreams are mocked with ``httpx.MockTransport`` injected through
``create_app`` — no network, no docker. JWTs are real HS256 tokens minted
with pyjwt against a test secret, so auth_verify exercises the same code
path production does.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

# Make `import app.*` resolve to gateway/app regardless of pytest's rootdir.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.middleware.rate_limit import RateLimiter  # noqa: E402

TEST_SECRET = "test-secret-not-for-production-0123456789"
FRONTEND_ORIGIN = "http://localhost:3000"

KHMER_REPLY = "ល្អណាស់! តោះគិតជំហានទីមួយជាមួយគ្នា។ 🐰"


def make_settings(**overrides) -> Settings:
    defaults = dict(
        auth_service_url="http://auth",
        orchestrator_url="http://orch",
        content_service_url="http://content",
        jwt_secret=TEST_SECRET,
        jwt_algorithm="HS256",
        frontend_origin=FRONTEND_ORIGIN,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def make_token(
    student_id: str = "student-1",
    *,
    secret: str = TEST_SECRET,
    expires_in_seconds: int = 3600,
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": student_id,
            "student_name": "សុជា (Sochea)",
            "school_code": "TUNSAY-G4-DEMO",
            "grade": 4,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in_seconds),
        },
        secret,
        algorithm="HS256",
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class FakeUpstreams:
    """One MockTransport handler for all three services, keyed by URL host.

    Records every request so tests can assert on exactly what the upstream
    received (the forged-student_id and case-translation assertions).
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def last_json(self) -> dict:
        return json.loads(self.requests[-1].content)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        host, path = request.url.host, request.url.path

        if path == "/health":
            return httpx.Response(200, json={"status": "ok", "service": host})

        if host == "orch" and path == "/chat":
            body = json.loads(request.content) if request.content else {}
            return httpx.Response(
                200,
                json={
                    "text_khmer": KHMER_REPLY,
                    "text_eng": "",
                    "is_safety_refusal": False,
                    "is_parent_help": False,
                    "session_id": body.get("session_id", "sess-1"),
                    "suggested_next": None,
                },
            )

        if host == "auth" and path == "/login":
            return httpx.Response(
                200,
                json={
                    "access_token": "issued-token",
                    "token_type": "bearer",
                    "user_profile": {"student_name": "សុជា (Sochea)", "grade": 4},
                },
            )

        if host == "auth" and path == "/me":
            return httpx.Response(
                200, json={"student_name": "សុជា (Sochea)", "school_code": "TUNSAY-G4-DEMO"}
            )

        if host == "content" and path == "/problems":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "math-g4-apples",
                        "title_khmer": "ចែកផ្លែប៉ោម",
                        "title_eng": "Sharing Apples",
                        "steps": [{"step_number": 1, "input_format": "mcq"}],
                    }
                ],
            )

        if host == "content" and path.startswith("/problems/"):
            return httpx.Response(
                200,
                json={
                    "id": path.rsplit("/", 1)[1],
                    "title_khmer": "ចែកផ្លែប៉ោម",
                    "title_eng": "Sharing Apples",
                },
            )

        return httpx.Response(404, json={"detail": "not found upstream"})


@pytest.fixture()
def upstreams() -> FakeUpstreams:
    return FakeUpstreams()


@pytest.fixture()
def clock():
    """Manual clock for the rate limiter: call ``clock.advance(seconds)``."""

    class Clock:
        def __init__(self) -> None:
            self.now = time.monotonic()

        def __call__(self) -> float:
            return self.now

        def advance(self, seconds: float) -> None:
            self.now += seconds

    return Clock()


@pytest.fixture()
def client(upstreams, clock) -> TestClient:
    settings = make_settings()
    app = create_app(
        settings=settings,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(upstreams.handler)),
        rate_limiter=RateLimiter(limit=20, window_seconds=60.0, clock=clock),
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def down_client() -> TestClient:
    """A gateway whose every upstream connection fails."""

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    app = create_app(
        settings=make_settings(),
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(refuse)),
        rate_limiter=RateLimiter(limit=20, window_seconds=60.0),
    )
    with TestClient(app) as test_client:
        yield test_client
