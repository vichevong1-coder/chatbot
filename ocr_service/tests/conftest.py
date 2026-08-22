"""Test fixtures for ocr_service."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from app.core.math_ocr import MathOcrEngine
from app.main import create_app


class FakeMathOcrEngine(MathOcrEngine):
    """Test fake for MathOcrEngine returning predictable results without network access."""

    def __init__(self, result: dict[str, Any] | None = None) -> None:
        super().__init__(api_key=None)
        self.result = result or {
            "text_khmer": "គណនា៖ ៥ + ៣ = ?",
            "text_eng": "Calculate: 5 + 3 = ?",
            "math_expressions": ["5 + 3 = ?"],
            "confidence": 0.98,
        }
        self.calls: list[dict[str, Any]] = []

    async def extract(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        self.calls.append({
            "bytes_len": len(image_bytes),
            "filename": filename,
            "mime_type": mime_type,
        })
        return dict(self.result)


@pytest.fixture
def fake_engine() -> FakeMathOcrEngine:
    return FakeMathOcrEngine()


@pytest.fixture
def client(fake_engine: FakeMathOcrEngine) -> TestClient:
    app = create_app(ocr_engine=fake_engine)
    return TestClient(app)


def make_test_image(
    width: int = 200,
    height: int = 100,
    fmt: str = "PNG",
    mode: str = "RGB",
    color: tuple = (255, 255, 255),
) -> bytes:
    """Helper to generate in-memory test images."""
    img = Image.new(mode, (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def png_image_bytes() -> bytes:
    return make_test_image(200, 100, "PNG", "RGB", (200, 220, 240))


@pytest.fixture
def jpeg_image_bytes() -> bytes:
    return make_test_image(300, 200, "JPEG", "RGB", (255, 255, 255))


@pytest.fixture
def webp_image_bytes() -> bytes:
    return make_test_image(150, 150, "WEBP", "RGB", (100, 150, 200))


@pytest.fixture
def rgba_image_bytes() -> bytes:
    return make_test_image(100, 100, "PNG", "RGBA", (255, 0, 0, 128))
