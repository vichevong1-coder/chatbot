"""API tests: /health and a full /explain happy path with an injected fake call."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import explain as explain_api
from app.main import create_app


@pytest.fixture
def client(generator):
    """TestClient with the fake-call generator installed via the test seam."""
    explain_api.set_generator(generator)
    try:
        with TestClient(create_app()) as test_client:
            yield test_client
    finally:
        explain_api.set_generator(None)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "pedagogy_service"}


def test_explain_happy_path_km(client, fake_call):
    response = client.post(
        "/explain",
        json={
            "prompt": "ហេតុអ្វីខ្ញុំគុណ?",
            "grade": 4,
            "language": "km",
            "mode": "student",
            "context": "Step 1: count the apples",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "text_khmer": fake_call.text,
        "text_eng": "",
        "from_fallback": False,
        "prompt_tokens": 11,
        "output_tokens": 7,
    }
    # The assembled system instruction went to the model, context rode along.
    sent = fake_call.calls[-1]
    assert "Tunsay (ទន្សាយ)" in sent["system_instruction"]
    assert "Context: Step 1: count the apples" in sent["prompt"]


def test_explain_happy_path_en(client, fake_call):
    fake_call.text = "Let's solve it together! 🐰"
    response = client.post(
        "/explain",
        json={"prompt": "why?", "grade": 6, "language": "en", "mode": "parent", "context": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text_eng"] == fake_call.text
    assert body["text_khmer"] == ""
    assert "Mode: parent." in fake_call.calls[-1]["system_instruction"]


def test_explain_grade_out_of_structural_bounds_rejected(client):
    response = client.post(
        "/explain",
        json={"prompt": "hi", "grade": 13, "language": "km", "mode": "student"},
    )
    assert response.status_code == 422


def test_explain_no_api_key_falls_back(fallback_generator):
    explain_api.set_generator(fallback_generator)
    try:
        with TestClient(create_app()) as test_client:
            response = test_client.post(
                "/explain",
                json={"prompt": "hi", "grade": 5, "language": "en", "mode": "student"},
            )
    finally:
        explain_api.set_generator(None)
    assert response.status_code == 200
    body = response.json()
    assert body["from_fallback"] is True
    assert body["text_eng"].startswith("No problem!")
    assert body["text_khmer"] == ""
