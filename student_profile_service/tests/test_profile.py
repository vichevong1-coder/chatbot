"""Unit tests for the student profile service endpoints and DB logic."""

from __future__ import annotations


def test_get_profile_creates_default_profile(client):
    """Retrieving a non-existent profile auto-creates it with 0 values."""
    response = client.get("/profile/test-student-id")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "test-student-id"
    assert data["stars"] == 0
    assert data["completed_problems_count"] == 0
    assert data["mastery_levels"] == {}


def test_record_attempt_updates_mastery_and_stars(client):
    """Submitting a correct answer attempt updates stars, completed problems, and mastery."""
    # 1. First record a correct attempt on the seeded step (step-1 of 1 total_steps)
    payload = {
        "student_id": "test-student-id",
        "problem_id": "math-g4-apples",
        "step_id": "step-1",
        "is_correct": True,
        "student_answer": "5",
        "session_id": "session-123",
        "misconception_code": None,
        "hint_rung_used": None,
    }
    response = client.post("/profile/attempts", json=payload)
    assert response.status_code == 201
    assert response.json() == {"status": "recorded"}

    # 2. Check updated profile statistics
    profile_resp = client.get("/profile/test-student-id")
    assert profile_resp.status_code == 200
    data = profile_resp.json()
    assert data["stars"] == 2
    assert data["completed_problems_count"] == 1
    assert data["mastery_levels"]["multiplication"] == 0.1

    # 3. Log a wrong attempt to decay mastery
    payload["is_correct"] = False
    payload["student_answer"] = "13"
    payload["misconception_code"] = "operation_confusion"
    response = client.post("/profile/attempts", json=payload)
    assert response.status_code == 201

    profile_resp = client.get("/profile/test-student-id")
    data = profile_resp.json()
    # Mastery should drop from 0.1 -> 0.05
    assert data["mastery_levels"]["multiplication"] == 0.05


def test_use_hint_deducts_stars(client):
    """Opening hints deducts stars, but never lets them fall below zero."""
    # 1. Earn 2 stars first
    payload = {
        "student_id": "test-student-id",
        "problem_id": "math-g4-apples",
        "step_id": "step-1",
        "is_correct": True,
    }
    client.post("/profile/attempts", json=payload)

    # 2. Consume a rung-1 hint (cost: 1 star)
    hint_payload = {
        "student_id": "test-student-id",
        "problem_id": "math-g4-apples",
        "step_id": "step-1",
        "rung": 1,
    }
    response = client.post("/profile/hints", json=hint_payload)
    assert response.status_code == 200
    assert response.json() == {"success": True, "remaining_stars": 1}

    # 3. Consume a rung-2 hint (cost: 2 stars)
    hint_payload["rung"] = 2
    response = client.post("/profile/hints", json=hint_payload)
    assert response.status_code == 200
    # Floor is 0 stars
    assert response.json() == {"success": True, "remaining_stars": 0}
