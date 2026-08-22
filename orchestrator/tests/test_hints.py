"""Integration tests for the /hints endpoint and progressive hint node."""

from __future__ import annotations

from conftest import PEDAGOGY_KHMER, post_chat


def post_hint(
    client,
    problem_id: str = "math-g4-apples",
    step_id: str = "apples-step-1",
    hint_level: int = 1,
    language: str = "km",
    session_id: str = "sess-hint-1",
):
    return client.post(
        "/hints",
        json={
            "session_id": session_id,
            "problem_id": problem_id,
            "step_id": step_id,
            "hint_level": hint_level,
            "language": language,
        },
    )


def test_post_hints_returns_ai_hint(client, fakes):
    response = post_hint(client, hint_level=1)
    assert response.status_code == 200
    body = response.json()
    assert body["hint_khmer"] == PEDAGOGY_KHMER
    assert body["hint_level"] == 1
    assert len(fakes.pedagogy.calls) == 1
    call = fakes.pedagogy.calls[0]
    assert "HINT LEVEL 1" in call["context"]
    assert call["grade"] == 4


def test_post_hints_level_3(client, fakes):
    response = post_hint(client, hint_level=3)
    assert response.status_code == 200
    body = response.json()
    assert body["hint_level"] == 3
    call = fakes.pedagogy.calls[0]
    assert "HINT LEVEL 3" in call["context"]


def test_post_hints_unknown_problem_404(client, fakes):
    response = post_hint(client, problem_id="nonexistent-prob")
    assert response.status_code == 404


def test_post_hints_unknown_step_404(client, fakes):
    response = post_hint(client, step_id="nonexistent-step")
    assert response.status_code == 404


def test_chat_progressive_hint_flow(client, fakes):
    response = post_chat(client, "give me a hint", problem_id="math-g4-apples")
    assert response.status_code == 200
    assert len(fakes.pedagogy.calls) == 1
    call = fakes.pedagogy.calls[0]
    assert "HINT LEVEL 1" in call["context"]
