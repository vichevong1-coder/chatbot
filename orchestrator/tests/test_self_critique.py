"""Unit tests for Self-Critique & Socratic Reflection Node."""

from __future__ import annotations

import pytest
from app.core.graph.nodes.self_critique import evaluate_response, self_critique_node

pytestmark = pytest.mark.anyio


def test_evaluate_response_passes_socratic_student_question():
    res = evaluate_response(
        response_text="តើអ្នកគិតថាខ្ទង់ភាគដប់ស្មើប៉ុន្មាន?",
        mode="student",
        correct_answer="55",
    )
    assert res["passed"] is True
    assert res["issues"] == []


def test_evaluate_response_detects_answer_leak():
    res = evaluate_response(
        response_text="The answer is 55! Good job.",
        mode="student",
        correct_answer="55",
    )
    assert res["passed"] is False
    assert any("leak" in issue.lower() for issue in res["issues"])


def test_evaluate_response_allows_answer_in_parent_mode():
    res = evaluate_response(
        response_text="The answer is 55! Explain to your child by adding 50 + 5.",
        mode="parent",
        correct_answer="55",
    )
    assert res["passed"] is True


async def test_self_critique_node():
    state = {
        "text_khmer": "តើ ២២ គុណ ៥ ស្មើប៉ុន្មានដែរ?",
        "mode": "student",
        "correct_answer": "110",
    }
    res = await self_critique_node(state)
    assert res["critique_passed"] is True
    assert res["critique_issues"] == []
