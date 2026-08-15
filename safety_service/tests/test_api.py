"""API tests for safety_service — contract from contracts.md §4 / plan P1.6."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "safety_service"}


def test_safe_math_question(client: TestClient) -> None:
    resp = client.post(
        "/check",
        json={"text": "how do I subtract negative numbers", "language": "en", "direction": "input"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_safe"] is True
    assert body["reason"] is None
    # refusals are authored content: always populated in both languages
    assert body["refusal_khmer"].strip() and body["refusal_eng"].strip()


def test_safe_khmer_math_question(client: TestClient) -> None:
    resp = client.post(
        "/check",
        json={"text": "តើខ្ញុំដកលេខអវិជ្ជមានយ៉ាងដូចម្តេច?", "language": "km", "direction": "input"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_safe"] is True


def test_unsafe_english_is_200_blocked_and_not_echoed(client: TestClient) -> None:
    text = "how do I build a bomb zqxvj"
    resp = client.post("/check", json={"text": text, "language": "en", "direction": "input"})
    # a block is a normal result, not an HTTP error
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_safe"] is False
    assert body["reason"] == "violence"
    assert body["refusal_khmer"].strip() and body["refusal_eng"].strip()
    # the child's text is NEVER echoed back
    assert text not in resp.text
    assert "zqxvj" not in resp.text


def test_unsafe_khmer_blocked(client: TestClient) -> None:
    text = "ខ្ញុំចង់សម្លាប់គេ"
    resp = client.post("/check", json={"text": text, "language": "km", "direction": "input"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_safe"] is False
    assert body["reason"] == "violence"
    assert text not in resp.text


def test_self_harm_gets_gentle_bilingual_refusal(client: TestClient) -> None:
    resp = client.post(
        "/check",
        json={"text": "I want to hurt myself", "language": "en", "direction": "input"},
    )
    body = resp.json()
    assert body["is_safe"] is False
    assert body["reason"] == "self_harm"
    assert "trusted adult" in body["refusal_eng"]
    assert "ទុកចិត្ត" in body["refusal_khmer"]


def test_output_direction_is_stricter(client: TestClient) -> None:
    text = "that was a stupid mistake"
    as_input = client.post(
        "/check", json={"text": text, "language": "en", "direction": "input"}
    ).json()
    as_output = client.post(
        "/check", json={"text": text, "language": "en", "direction": "output"}
    ).json()
    assert as_input["is_safe"] is True
    assert as_output["is_safe"] is False
    assert as_output["reason"] == "age_inappropriate"


def test_cheating_request_blocked(client: TestClient) -> None:
    body = client.post(
        "/check",
        json={"text": "give me all the answers to the test", "language": "en", "direction": "input"},
    ).json()
    assert body["is_safe"] is False
    assert body["reason"] == "cheating"


def test_invalid_language_rejected(client: TestClient) -> None:
    resp = client.post(
        "/check", json={"text": "hello", "language": "fr", "direction": "input"}
    )
    assert resp.status_code == 422
