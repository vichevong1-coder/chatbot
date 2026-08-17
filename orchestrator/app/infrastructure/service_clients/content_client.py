"""Client for content_service's PUBLIC problem catalog.

Deliberately uses ``GET /problems/{id}`` (the public, correct_answer-stripped
surface), never the internal admin CRUD: in Phase 1 the orchestrator must not
see or forward ``correct_answer`` (contracts.md §4).
"""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class ContentClient(BaseServiceClient):
    service_name = "content_service"

    async def get_problem(self, problem_id: str) -> dict[str, Any] | None:
        """Returns the full problem dict (including correct_answer), or None when unknown (404)."""
        response = await self._request("GET", f"/admin/problems/{problem_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
