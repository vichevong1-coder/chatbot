"""Client for retrieval_service."""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class RetrievalClient(BaseServiceClient):
    service_name = "retrieval_service"

    async def retrieve(
        self,
        query: str,
        grade: int | None = None,
        subject: str | None = None,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        response = await self._request(
            "POST",
            "/retrieve",
            json={
                "query": query,
                "grade": grade,
                "subject": subject,
                "top_k": top_k,
            },
        )
        response.raise_for_status()
        return response.json().get("results", [])
