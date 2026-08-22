"""Public and admin API over the seeded catalog.

The load-bearing assertion: nothing served on the public surface ever contains a
``correct_answer``, in either naming convention (.claude/contracts.md section 4).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.anyio


def assert_no_answers(response) -> None:
    body = response.text
    assert "correct_answer" not in body
    assert "correctAnswer" not in body


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "content_service"}


# ---------------------------------------------------------------- public surface


async def test_list_problems_public_shape(client):
    r = await client.get("/problems")
    assert r.status_code == 200
    problems = r.json()
    assert len(problems) == 9
    assert_no_answers(r)
    # Steps and their scaffolding are intact — only the answer key is stripped.
    apples = next(p for p in problems if p["id"] == "math-g4-apples")
    assert len(apples["steps"]) == 4
    assert apples["steps"][0]["hint1"]["khmer"]


async def test_list_problems_filters(client):
    r = await client.get("/problems", params={"grade": 4})
    assert {p["id"] for p in r.json()} == {
        "english-g4-grammar",
        "math-g4-apples",
        "math-g4-fractions",
        "science-g4-water",
    }

    r = await client.get("/problems", params={"subject": "math"})
    assert {p["id"] for p in r.json()} == {
        "math-g3-perimeter",
        "math-g4-apples",
        "math-g4-fractions",
        "math-g6-ratio",
    }

    r = await client.get("/problems", params={"grade": 4, "subject": "science"})
    assert {p["id"] for p in r.json()} == {"science-g4-water"}

    r = await client.get("/problems", params={"subject": "alchemy"})
    assert r.status_code == 422  # closed vocabulary


async def test_get_problem_public_khmer_intact(client):
    r = await client.get("/problems/math-g4-apples")
    assert r.status_code == 200
    assert_no_answers(r)
    problem = r.json()
    assert "៥" in problem["problem_statement_khmer"]  # Khmer numerals survive the DB
    assert problem["title_khmer"].startswith("ចំណោទគណិតវិទ្យា")
    # mcq options still ship (StepCard needs them); only the answer key is gone.
    mcq = problem["steps"][2]
    assert mcq["input_format"] == "mcq"
    assert len(mcq["options"]) == 3


async def test_get_problem_404_is_structured_and_bilingual(client):
    r = await client.get("/problems/no-such-problem")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["error"] == "problem_not_found"
    assert detail["problem_id"] == "no-such-problem"
    assert detail["message_khmer"]  # a child never sees an English-only error
    assert detail["message_eng"]


# ---------------------------------------------------------------- admin surface


async def test_admin_get_returns_answers(client):
    r = await client.get("/admin/problems/math-g4-apples")
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert steps[0]["correct_answer"] == "5"
    assert steps[3]["correct_answer"] == "40"


async def test_admin_upsert_reflected_publicly_but_still_stripped(client):
    full = (await client.get("/admin/problems/math-g4-apples")).json()
    full["title_eng"] = "Math Problem: Multiplication (v2)"
    full["steps"][3]["correct_answer"] = "40 "  # whitespace is stripped by the schema

    r = await client.post("/admin/problems", json=full)
    assert r.status_code == 200
    assert r.json()["title_eng"] == "Math Problem: Multiplication (v2)"

    r = await client.get("/problems/math-g4-apples")
    assert r.json()["title_eng"] == "Math Problem: Multiplication (v2)"
    assert_no_answers(r)

    r = await client.get("/admin/problems/math-g4-apples")
    assert r.json()["steps"][3]["correct_answer"] == "40"


async def test_admin_upsert_rejects_invalid_problem(client):
    full = (await client.get("/admin/problems/math-g4-apples")).json()
    for step in full["steps"]:
        step["total_steps"] = 9  # the science-g4-water class of defect
    r = await client.post("/admin/problems", json=full)
    assert r.status_code == 422
    # and the stored problem is untouched
    r = await client.get("/admin/problems/math-g4-apples")
    assert r.json()["steps"][0]["total_steps"] == 4


async def test_admin_delete_then_404(client):
    r = await client.delete("/admin/problems/math-g3-perimeter")
    assert r.status_code == 204
    assert (await client.get("/problems/math-g3-perimeter")).status_code == 404
    assert (await client.get("/admin/problems/math-g3-perimeter")).status_code == 404
    assert (await client.delete("/admin/problems/math-g3-perimeter")).status_code == 404
    # the rest of the catalog is untouched
    assert len((await client.get("/problems")).json()) == 8
