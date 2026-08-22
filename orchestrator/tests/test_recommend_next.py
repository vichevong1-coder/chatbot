"""Tests for recommend_next node and recommendation flow."""

from __future__ import annotations

import pytest

from app.core.graph.nodes.recommend_next import recommend_next
from conftest import post_chat


@pytest.mark.anyio
async def test_recommend_next_direct_node_call(fakes):
    state = {
        "student_id": "stu-1",
        "problem_id": "math-g4-apples",
        "language": "km",
    }
    result = await recommend_next(state, fakes)
    assert result["suggested_next"] == "math-g4-fractions"
    assert "ទន្សាយ" in result["text_khmer"]


@pytest.mark.anyio
async def test_recommend_next_prioritizes_lowest_mastery(fakes):
    fakes.profile.profile_data = {
        "stars": 10,
        "completed_problems": [],
        "completed_problems_count": 0,
        "mastery_levels": {
            "multiplication": 0.9,
            "fractions": 0.1,
        },
    }
    state = {
        "student_id": "stu-1",
        "language": "en",
    }
    result = await recommend_next(state, fakes)
    # Fractions has lower mastery (0.1 < 0.9)
    assert result["suggested_next"] == "math-g4-fractions"
    assert "Tunsay" in result["text_eng"]


@pytest.mark.anyio
async def test_recommend_next_filters_completed_problems(fakes):
    fakes.profile.profile_data = {
        "stars": 10,
        "completed_problems": ["math-g4-apples"],
        "completed_problems_count": 1,
        "mastery_levels": {},
    }
    state = {
        "student_id": "stu-1",
        "language": "en",
    }
    result = await recommend_next(state, fakes)
    assert result["suggested_next"] == "math-g4-fractions"


def test_recommend_next_chat_endpoint_english(client, fakes):
    response = post_chat(client, "what should i do next?", language="en")
    assert response.status_code == 200
    body = response.json()
    assert body["suggested_next"] in ("math-g4-apples", "math-g4-fractions")
    assert "Tunsay recommends" in body["text_eng"]
    assert body["text_khmer"] == ""


def test_recommend_next_chat_endpoint_khmer(client, fakes):
    response = post_chat(client, "សូមណែនាំលំហាត់បន្ទាប់", language="km")
    assert response.status_code == 200
    body = response.json()
    assert body["suggested_next"] in ("math-g4-apples", "math-g4-fractions")
    assert "ទន្សាយសូមណែនាំ" in body["text_khmer"]
    assert body["text_eng"] == ""


def test_recommend_next_profile_down_graceful(client, fakes):
    fakes.profile.down = True
    response = post_chat(client, "what should i do next?", language="en")
    assert response.status_code == 200
    body = response.json()
    # Still succeeds and returns a recommendation from available content
    assert body["suggested_next"] is not None


def test_recommend_next_content_down_graceful(client, fakes):
    fakes.content.down = True
    response = post_chat(client, "what should i do next?", language="en")
    assert response.status_code == 200
    body = response.json()
    assert body["suggested_next"] is None
    assert "couldn't find" in body["text_eng"]
