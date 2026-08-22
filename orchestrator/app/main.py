"""Orchestrator app factory (plan.md P1.7).

``create_app(clients=None, session_store=None)`` is the DI seam: tests inject
fake service clients and an InMemorySessionStore; production builds real httpx
clients from the ``*_SERVICE_URL`` environment variables (.env.example) and a
RedisSessionStore over ``dal.clients.redis``.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.answers import router as answers_router
from app.api.hints import router as hints_router
from app.api.chat_audio import router as chat_audio_router
from app.api.chat_image import router as chat_image_router
from app.core.graph.builder import build_graph
from app.infrastructure.service_clients import ServiceClients
from app.infrastructure.service_clients.auth_client import AuthClient
from app.infrastructure.service_clients.content_client import ContentClient
from app.infrastructure.service_clients.pedagogy_client import PedagogyClient
from app.infrastructure.service_clients.safety_client import SafetyClient
from app.infrastructure.service_clients.solver_client import SolverClient
from app.infrastructure.service_clients.grading_client import GradingClient
from app.infrastructure.service_clients.profile_client import ProfileClient
from app.infrastructure.service_clients.stt_client import SttClient
from app.infrastructure.service_clients.ocr_client import OcrClient
from app.infrastructure.service_clients.retrieval_client import RetrievalClient
from app.session_store.redis_store import RedisSessionStore, SessionStore
from app.utils.logging import request_id_var


def _default_clients(http: httpx.AsyncClient) -> ServiceClients:
    """Real clients over one shared AsyncClient; URLs per .env.example."""

    def url(name: str, default: str) -> str:
        return os.environ.get(name, default).strip() or default

    return ServiceClients(
        safety=SafetyClient(url("SAFETY_SERVICE_URL", "http://safety_service:9011"), http),
        solver=SolverClient(url("SOLVER_SERVICE_URL", "http://solver_service:9004"), http),
        content=ContentClient(url("CONTENT_SERVICE_URL", "http://content_service:9003"), http),
        pedagogy=PedagogyClient(
            url("PEDAGOGY_SERVICE_URL", "http://pedagogy_service:9006"), http
        ),
        auth=AuthClient(url("AUTH_SERVICE_URL", "http://auth_service:9002"), http),
        grading=GradingClient(url("GRADING_SERVICE_URL", "http://grading_service:9005"), http),
        profile=ProfileClient(url("PROFILE_SERVICE_URL", "http://student_profile_service:9008"), http),
        stt=SttClient(url("STT_SERVICE_URL", "http://stt_service:9009"), http),
        ocr=OcrClient(url("OCR_SERVICE_URL", "http://ocr_service:9010"), http),
        retrieval=RetrievalClient(url("RETRIEVAL_SERVICE_URL", "http://retrieval_service:9007"), http),
    )


def create_app(
    clients: ServiceClients | None = None,
    session_store: SessionStore | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if app.state.http is not None:
            await app.state.http.aclose()

    app = FastAPI(title="Tunsay orchestrator", lifespan=lifespan)

    if clients is None:
        app.state.http = httpx.AsyncClient()
        clients = _default_clients(app.state.http)
    else:
        app.state.http = None  # injected fakes own no transport

    app.state.clients = clients
    app.state.session_store = session_store or RedisSessionStore()
    app.state.graph = build_graph(clients)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """One uuid per request, carried into every structured log line."""
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(answers_router)
    app.include_router(hints_router)
    app.include_router(chat_audio_router)
    app.include_router(chat_image_router)
    return app


app = create_app()
