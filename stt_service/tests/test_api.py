"""Tests for stt_service API endpoints."""

from __future__ import annotations

import io


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "stt_service"}


def test_transcribe_khmer_audio(client):
    fake_audio = b"\x1a\x45\xdf\xa3fake-webm-data"
    res = client.post(
        "/transcribe",
        files={"file": ("speech.webm", io.BytesIO(fake_audio), "audio/webm")},
        data={"language": "km"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["language"] == "km"
    assert body["text"] == "៥ បូក ៣"
    assert body["normalized_math"] == "5 + 3"


def test_transcribe_english_audio(client):
    fake_audio = b"\x1a\x45\xdf\xa3fake-webm-data"
    res = client.post(
        "/transcribe",
        files={"file": ("speech.webm", io.BytesIO(fake_audio), "audio/webm")},
        data={"language": "en"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["language"] == "en"
    assert body["text"] == "5 plus 3"
    assert body["normalized_math"] == "5 + 3"


def test_transcribe_empty_file_fails(client):
    res = client.post(
        "/transcribe",
        files={"file": ("speech.webm", io.BytesIO(b""), "audio/webm")},
    )
    assert res.status_code == 400
