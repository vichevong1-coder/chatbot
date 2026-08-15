"""Client for solver_service ``POST /solve``.

422 (unparseable expression) raises SolverUnparseable so the solve node can
fall through to the explain path instead of failing the child's request.
"""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient, SolverUnparseable


class SolverClient(BaseServiceClient):
    service_name = "solver_service"

    async def solve(self, expression: str) -> dict[str, Any]:
        """Returns ``{expression, answer, steps}``."""
        response = await self._request("POST", "/solve", json={"expression": expression})
        if response.status_code == 422:
            raise SolverUnparseable(expression)
        response.raise_for_status()
        return response.json()
