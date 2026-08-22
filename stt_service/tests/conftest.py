"""Pytest fixtures for stt_service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from app.core.transcriber import AudioTranscriber
from app.main import create_app


class FakeTranscriber(AudioTranscriber):
    def __init__(self) -> None:
        super().__init__(api_key=None)

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm", preferred_language: str | None = None) -> dict:
        if not audio_bytes:
            from app.core.audio_preprocess import AudioValidationError
            raise AudioValidationError("Empty audio payload")
        lang = preferred_language or "km"
        if lang == "km":
            text = "៥ បូក ៣"
            norm = "5 + 3"
        else:
            text = "5 plus 3"
            norm = "5 + 3"
        return {"text": text, "language": lang, "normalized_math": norm}


@pytest.fixture
def client():
    app = create_app(transcriber=FakeTranscriber())
    return TestClient(app)
