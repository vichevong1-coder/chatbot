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
    assert resp.json() == {"status": "ok", "service": "grading_service"}

def test_grade_exact_match(client: TestClient) -> None:
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "5",
            "student_answer": "5",
            "input_format": "number"
        }
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["misconception_code"] is None

def test_grade_khmer_numerals(client: TestClient) -> None:
    # ៥ is Khmer digit 5
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "5",
            "student_answer": "៥",
            "input_format": "number"
        }
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["misconception_code"] is None

def test_grade_equivalent_fraction(client: TestClient) -> None:
    # 0.5 vs 1/2 vs 2/4
    resp1 = client.post(
        "/grade",
        json={
            "correct_answer": "1/2",
            "student_answer": "0.5",
            "input_format": "number"
        }
    )
    assert resp1.json()["is_correct"] is True

    resp2 = client.post(
        "/grade",
        json={
            "correct_answer": "0.5",
            "student_answer": "2/4",
            "input_format": "number"
        }
    )
    assert resp2.json()["is_correct"] is True

def test_misconception_place_value(client: TestClient) -> None:
    # off by factor of 10
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "40",
            "student_answer": "400",
            "input_format": "number"
        }
    )
    body = resp.json()
    assert body["is_correct"] is False
    assert body["misconception_code"] == "place_value_error"

def test_misconception_off_by_one(client: TestClient) -> None:
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "40",
            "student_answer": "39",
            "input_format": "number"
        }
    )
    body = resp.json()
    assert body["is_correct"] is False
    assert body["misconception_code"] == "off_by_one"

def test_misconception_unit_omission(client: TestClient) -> None:
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "5 kg",
            "student_answer": "5",
            "input_format": "number"
        }
    )
    body = resp.json()
    assert body["is_correct"] is False
    assert body["misconception_code"] == "unit_omission"

def test_misconception_operation_confusion(client: TestClient) -> None:
    # 5 * 8 is 40. Student added them: 5 + 8 = 13.
    resp = client.post(
        "/grade",
        json={
            "correct_answer": "40",
            "student_answer": "13",
            "input_format": "number",
            "question_text": "Calculate 5 times 8"
        }
    )
    body = resp.json()
    assert body["is_correct"] is False
    assert body["misconception_code"] == "operation_confusion"
