"""Client for safety_service ``POST /check`` (contracts.md §4).

The caller (safety_gate) fails CLOSED when this raises ServiceUnavailable —
unchecked text must never reach the LLM (claude.md §4).
"""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class SafetyClient(BaseServiceClient):
    service_name = "safety_service"

    async def check(
        self, text: str, language: str, direction: str = "input"
    ) -> dict[str, Any]:
        """Returns ``{is_safe, reason, refusal_khmer, refusal_eng}``."""
        response = await self._request(
            "POST",
            "/check",
            json={"text": text, "language": language, "direction": direction},
        )
        return response.json()
