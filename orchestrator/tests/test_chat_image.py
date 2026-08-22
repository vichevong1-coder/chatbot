"""Tests for POST /chat/image endpoint in orchestrator."""

from __future__ import annotations

import io
import pytest
from PIL import Image

from conftest import APPLES_PROBLEM


def make_test_image(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_chat_image_success(client, fakes, store):
    img_bytes = make_test_image()
    files = {"file": ("homework.jpg", img_bytes, "image/jpeg")}
    data = {
        "session_id": "test-ocr-sess-1",
        "student_id": "student-123",
        "language": "km",
        "mode": "student",
    }

    response = client.post("/chat/image", files=files, data=data)
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "test-ocr-sess-1"
    assert "text_khmer" in body
    assert body["is_safety_refusal"] is False

    # Check transcript
    transcript = store.sessions.get("test-ocr-sess-1", [])
    assert len(transcript) == 2
    assert transcript[0]["sender"] == "user"
    assert transcript[0]["image_uri"] == "homework.jpg"
    assert transcript[1]["sender"] == "sayo"


def test_chat_image_with_matched_problem(client, fakes, store):
    img_bytes = make_test_image()
    files = {"file": ("problem.jpg", img_bytes, "image/jpeg")}
    data = {
        "session_id": "test-ocr-sess-2",
        "student_id": "student-123",
        "language": "km",
        "mode": "student",
        "problem_id": "math-g4-apples",
    }

    response = client.post("/chat/image", files=files, data=data)
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "test-ocr-sess-2"


def test_chat_image_empty_file_fails(client):
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    data = {
        "session_id": "test-ocr-sess-3",
        "student_id": "student-123",
    }
    response = client.post("/chat/image", files=files, data=data)
    assert response.status_code == 400
    assert "Empty image payload" in response.json()["detail"]


def test_chat_image_ocr_service_down_graceful_fallback(client, fakes, store):
    fakes.ocr.down = True
    img_bytes = make_test_image()
    files = {"file": ("homework.jpg", img_bytes, "image/jpeg")}
    data = {
        "session_id": "test-ocr-sess-down",
        "student_id": "student-123",
        "language": "km",
    }

    response = client.post("/chat/image", files=files, data=data)
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "test-ocr-sess-down"
