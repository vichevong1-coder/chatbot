"""Client for pedagogy_service ``POST /explain`` — the only Gemini-backed call."""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class PedagogyClient(BaseServiceClient):
    service_name = "pedagogy_service"

    async def explain(
        self,
        *,
        prompt: str,
        grade: int,
        language: str,
        mode: str,
        context: str | None = None,
        misconception_code: str | None = None,
    ) -> dict[str, Any]:
        """Returns ``{text_khmer, text_eng, from_fallback, ...}``."""
        response = await self._request(
            "POST",
            "/explain",
            json={
                "prompt": prompt,
                "grade": grade,
                "language": language,
                "mode": mode,
                "context": context,
                "misconception_code": misconception_code,
            },
            timeout=45.0,
        )
        response.raise_for_status()
        return response.json()

    async def translate(
        self,
        *,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> dict[str, Any]:
        """Returns ``{translated_text, target_language, from_fallback}``."""
        response = await self._request(
            "POST",
            "/translate",
            json={
                "text": text,
                "target_language": target_language,
                "source_language": source_language,
            },
        )
        response.raise_for_status()
        return response.json()
