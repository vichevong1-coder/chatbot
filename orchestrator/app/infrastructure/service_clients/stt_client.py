"""Client for stt_service."""

from __future__ import annotations

from typing import Any
import httpx

from . import BaseServiceClient


class SttClient(BaseServiceClient):
    service_name = "stt_service"

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: str | None = None,
    ) -> dict[str, Any]:
        files = {"file": (filename, audio_bytes, "audio/webm")}
        data = {"language": language} if language else {}
        response = await self._request(
            "POST",
            "/transcribe",
            files=files,
            data=data,
        )
        response.raise_for_status()
        return response.json()
