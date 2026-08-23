"""Unit and integration tests for ocr_service."""

from __future__ import annotations

import io
import pytest
from PIL import Image

from app.core.image_preprocess import (
    ImageValidationError,
    validate_and_preprocess_image,
)
from app.core.math_ocr import MathOcrEngine, extract_math_expressions
from conftest import FakeMathOcrEngine, make_test_image


# ==========================================
# 1. Image Preprocessing Tests
# ==========================================

def test_preprocess_valid_png(png_image_bytes: bytes):
    result = validate_and_preprocess_image(png_image_bytes, filename="test.png")
    assert result.format == "jpeg"
    assert result.width == 200
    assert result.height == 100
    assert result.mime_type == "image/jpeg"
    assert len(result.image_bytes) > 0


def test_preprocess_valid_jpeg(jpeg_image_bytes: bytes):
    result = validate_and_preprocess_image(jpeg_image_bytes, filename="test.jpg")
    assert result.format == "jpeg"
    assert result.width == 300
    assert result.height == 200
    assert result.mime_type == "image/jpeg"
    assert len(result.image_bytes) > 0


def test_preprocess_valid_webp(webp_image_bytes: bytes):
    result = validate_and_preprocess_image(webp_image_bytes, filename="test.webp")
    assert result.format == "jpeg"
    assert result.width == 150
    assert result.height == 150
    assert result.mime_type == "image/jpeg"
    assert len(result.image_bytes) > 0


def test_preprocess_rgba_converts_to_rgb(rgba_image_bytes: bytes):
    result = validate_and_preprocess_image(rgba_image_bytes, filename="transparent.png")
    assert result.format == "jpeg"
    assert result.width == 100
    assert result.height == 100
    # Reopen to verify mode is RGB
    reopened = Image.open(io.BytesIO(result.image_bytes))
    assert reopened.mode == "RGB"


def test_preprocess_downscales_oversized_image():
    # 3000 x 1500 should be downscaled to max dimension 2048
    big_img_bytes = make_test_image(3000, 1500, "JPEG")
    result = validate_and_preprocess_image(big_img_bytes)
    assert result.width == 2048
    assert result.height == 1024


def test_preprocess_rejects_empty_bytes():
    with pytest.raises(ImageValidationError, match="Empty image payload"):
        validate_and_preprocess_image(b"")


def test_preprocess_rejects_corrupted_data():
    with pytest.raises(ImageValidationError, match="Invalid or corrupted image"):
        validate_and_preprocess_image(b"not-an-image-file-contents")


def test_preprocess_rejects_too_small_dimension():
    tiny_bytes = make_test_image(5, 5, "PNG")
    with pytest.raises(ImageValidationError, match="Image dimensions too small"):
        validate_and_preprocess_image(tiny_bytes)


def test_preprocess_rejects_payload_exceeding_max_bytes():
    dummy_bytes = make_test_image(50, 50, "PNG")
    with pytest.raises(ImageValidationError, match="Image payload exceeds maximum allowed size"):
        validate_and_preprocess_image(dummy_bytes, max_size=10)


# ==========================================
# 2. Math OCR Logic & Helpers Tests
# ==========================================

def test_extract_math_expressions():
    text = (
        "សូមគណនាលំហាត់ខាងក្រោម៖\n"
        "៥ + ៣ = ?\n"
        "១២ / ៤ = ៣\n"
        "2x + 5 = 15\n"
        "អរគុណច្រើន"
    )
    expressions = extract_math_expressions(text)
    assert any("៥ + ៣" in expr or "5 + 3" in expr for expr in expressions) or "៥ + ៣ = ?" in expressions
    assert "2x + 5 = 15" in expressions


def test_extract_math_expressions_empty():
    assert extract_math_expressions("") == []
    assert extract_math_expressions("គ្មានលេខទេ") == []


@pytest.mark.anyio
async def test_math_ocr_engine_offline_fallback(jpeg_image_bytes: bytes):
    engine = MathOcrEngine(api_key=None)
    result = await engine.extract(jpeg_image_bytes)
    assert "text_khmer" in result
    assert "text_eng" in result
    assert "math_expressions" in result
    assert isinstance(result["math_expressions"], list)
    assert result["confidence"] == 1.0


# ==========================================
# 3. API Route Tests (FastAPI /health & /extract)
# ==========================================

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "service": "ocr_service"}


def test_extract_endpoint_success(client, png_image_bytes: bytes):
    files = {"file": ("homework.png", png_image_bytes, "image/png")}
    response = client.post("/extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["text_khmer"] == "គណនា៖ ៥ + ៣ = ?"
    assert data["text_eng"] == "Calculate: 5 + 3 = ?"
    assert data["math_expressions"] == ["5 + 3 = ?"]
    assert data["confidence"] == 0.98


def test_extract_endpoint_invalid_file(client):
    files = {"file": ("corrupt.png", b"invalid-bytes", "image/png")}
    response = client.post("/extract", files=files)
    assert response.status_code == 400
    assert "detail" in response.json()


def test_extract_endpoint_empty_file(client):
    files = {"file": ("empty.png", b"", "image/png")}
    response = client.post("/extract", files=files)
    assert response.status_code == 400
    assert "Empty image payload" in response.json()["detail"]
