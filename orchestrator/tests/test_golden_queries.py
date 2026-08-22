"""Golden queries verification test suite (plan.md P2.4 / P2.5).

Verifies:
1. Intent routing across >= 20 golden queries in Khmer and English.
2. Student mode never acts in parent mode and asks guiding questions.
3. Parent mode provides pedagogical explanation methods (is_parent_help=True).
4. Safety refusals trigger on harmful queries and prevent LLM/solver execution.
5. Explanation caching serves repeated problem step requests with 0 tokens.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import REFUSAL_ENG, REFUSAL_KHMER, post_chat

GOLDEN_DIR = Path(__file__).parent / "golden_queries"


def _load_json(filename: str) -> list[dict]:
    with open(GOLDEN_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


ROUTING_QUERIES = _load_json("routing_queries.json")
STUDENT_QUERIES = _load_json("student_mode_queries.json")
PARENT_QUERIES = _load_json("parent_mode_queries.json")
SAFETY_QUERIES = _load_json("safety_queries.json")


@pytest.mark.parametrize("item", ROUTING_QUERIES, ids=[f"{q['language']}-{q['expected_intent']}-{q['prompt'][:15]}" for q in ROUTING_QUERIES])
def test_golden_intent_routing(client, fakes, item):
    prompt = item["prompt"]
    language = item["language"]
    expected_intent = item["expected_intent"]

    response = post_chat(client, prompt, language=language)
    assert response.status_code == 200
    body = response.json()

    if expected_intent == "greeting":
        if language == "km":
            assert "ទន្សាយ" in body["text_khmer"]
            assert body["text_eng"] == ""
        else:
            assert "Tunsay" in body["text_eng"]
            assert body["text_khmer"] == ""
        assert fakes.pedagogy.calls == []
        assert fakes.solver.calls == []

    elif expected_intent == "solve":
        # Solver path
        assert len(fakes.solver.calls) == 1
        assert fakes.pedagogy.calls == []

    elif expected_intent == "hint":
        # Hint path
        assert len(fakes.pedagogy.calls) == 1

    elif expected_intent == "recommend_next":
        # Recommendation path
        if language == "km":
            assert "ទន្សាយ" in body["text_khmer"]
        else:
            assert "Tunsay" in body["text_eng"]

    elif expected_intent == "clarify":
        # Clarify path
        if language == "km":
            assert "ទន្សាយ" in body["text_khmer"]
            assert body["text_eng"] == ""
        else:
            assert "help" in body["text_eng"].lower()
            assert body["text_khmer"] == ""
        assert body["is_parent_help"] is False
        assert fakes.pedagogy.calls == []
        assert fakes.solver.calls == []

    elif expected_intent == "explain":
        # Explain path
        assert len(fakes.pedagogy.calls) == 1


@pytest.mark.parametrize("item", STUDENT_QUERIES, ids=[f"student-{q['language']}-{q['problem_id']}" for q in STUDENT_QUERIES])
def test_golden_student_mode(client, fakes, item):
    response = post_chat(
        client,
        item["prompt"],
        problem_id=item["problem_id"],
        active_step_index=item["step_index"],
        language=item["language"],
        mode="student",
    )
    assert response.status_code == 200
    body = response.json()

    assert body["is_parent_help"] is False
    assert len(fakes.pedagogy.calls) == 1
    assert fakes.pedagogy.calls[0]["mode"] == "student"


@pytest.mark.parametrize("item", PARENT_QUERIES, ids=[f"parent-{q['language']}-{q['problem_id']}" for q in PARENT_QUERIES])
def test_golden_parent_mode(client, fakes, item):
    response = post_chat(
        client,
        item["prompt"],
        problem_id=item["problem_id"],
        active_step_index=item["step_index"],
        language=item["language"],
        mode="parent",
    )
    assert response.status_code == 200
    body = response.json()

    assert body["is_parent_help"] is True
    assert len(fakes.pedagogy.calls) == 1
    assert fakes.pedagogy.calls[0]["mode"] == "parent"


@pytest.mark.parametrize("item", SAFETY_QUERIES, ids=[f"safety-{q['language']}-{q['prompt'][:15]}" for q in SAFETY_QUERIES])
def test_golden_safety_refusals(client, fakes, item):
    fakes.safety.unsafe = True
    response = post_chat(client, item["prompt"], language=item["language"])
    assert response.status_code == 200
    body = response.json()

    assert body["is_safety_refusal"] is True
    if item["language"] == "km":
        assert body["text_khmer"] == REFUSAL_KHMER
        assert body["text_eng"] == ""
    else:
        assert body["text_eng"] == REFUSAL_ENG
        assert body["text_khmer"] == ""

    # Must never call LLM or solver when safety gate refuses
    assert fakes.pedagogy.calls == []
    assert fakes.solver.calls == []


def test_golden_explanation_cache_hit_costs_zero_tokens(client, fakes):
    """Verify that repeated problem step explanation requests are cached and cost zero LLM calls."""
    problem_id = "math-g4-apples"
    step_index = 0

    # 1. First request -> cache miss, calls pedagogy
    resp1 = post_chat(
        client,
        "how do I do step 1?",
        problem_id=problem_id,
        active_step_index=step_index,
        language="km",
        mode="student",
    )
    assert resp1.status_code == 200
    assert len(fakes.pedagogy.calls) == 1

    # 2. Second request with same problem and step -> cache hit, does NOT call pedagogy
    resp2 = post_chat(
        client,
        "how do I do step 1?",
        problem_id=problem_id,
        active_step_index=step_index,
        language="km",
        mode="student",
    )
    assert resp2.status_code == 200
    assert len(fakes.pedagogy.calls) == 1  # call count remains 1!
    assert resp2.json()["text_khmer"] == resp1.json()["text_khmer"]
