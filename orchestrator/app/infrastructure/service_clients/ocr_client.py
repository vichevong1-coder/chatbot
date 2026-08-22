"""Client for ocr_service POST /extract."""

from __future__ import annotations

from typing import Any

from . import BaseServiceClient


class OcrClient(BaseServiceClient):
    service_name = "ocr_service"

    async def extract(
        self, image_bytes: bytes, filename: str = "image.jpg"
    ) -> dict[str, Any]:
        """Send image to ocr_service and return extracted text, math expressions, and confidence."""
        files = {
            "file": (filename, image_bytes, "image/jpeg")
        }
        response = await self._request("POST", "/extract", files=files)
        response.raise_for_status()
        return response.json()
