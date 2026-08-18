"""Typed clients for the services the orchestrator fans out to.

Only the orchestrator fans out (architecture.md §1 rule 2). One small class per
service, all sharing a single ``httpx.AsyncClient``; base URLs come from the
``*_SERVICE_URL`` environment variables in ``.env.example``.

Errors: connect failures and 5xx raise :class:`ServiceUnavailable`, which each
graph node converts into a child-safe outcome (safety → fail-closed refusal,
pedagogy → bilingual fallback, solver → fall through to explain, content →
explain without context). A child must never see a stack trace (claude.md §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_TIMEOUT_SECONDS = 10.0


class ServiceUnavailable(Exception):
    """The downstream service is down or answered 5xx."""

    def __init__(self, service: str, detail: str = "") -> None:
        self.service = service
        super().__init__(f"{service} unavailable: {detail}" if detail else f"{service} unavailable")


class SolverUnparseable(Exception):
    """solver_service answered 422 — the expression is not bare arithmetic."""


@dataclass
class ServiceClients:
    """The set of clients the Phase-1 graph needs, injectable for tests.

    Fields are duck-typed on purpose — tests inject plain fakes with the same
    method signatures. The other five services (grading, retrieval, profile,
    stt, ocr) join in later phases; their client modules stay empty stubs.
    """

    safety: Any
    solver: Any
    content: Any
    pedagogy: Any
    auth: Any
    grading: Any
    profile: Any


class BaseServiceClient:
    """Shared POST/GET plumbing over one ``httpx.AsyncClient``."""

    service_name = "unknown"

    def __init__(self, base_url: str, http: httpx.AsyncClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._http = http

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self._base_url}{path}"
        try:
            response = await self._http.request(
                method, url, timeout=DEFAULT_TIMEOUT_SECONDS, **kwargs
            )
        except httpx.HTTPError as exc:
            raise ServiceUnavailable(self.service_name, str(exc)) from exc
        if response.status_code >= 500:
            raise ServiceUnavailable(self.service_name, f"HTTP {response.status_code}")
        return response
