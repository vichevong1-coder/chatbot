"""Client for auth_service — minimal placeholder.

Token verification happens at the gateway (plan.md P1.9); the orchestrator will
use ``get_me`` later to fetch the student's grade for pedagogy (see the TODO in
nodes/explain.py). Kept minimal on purpose.
"""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class AuthClient(BaseServiceClient):
    service_name = "auth_service"

    async def get_me(self, token: str) -> dict[str, Any]:
        """Returns the authenticated student's profile."""
        response = await self._request(
            "GET", "/me", headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
