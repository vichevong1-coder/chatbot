"""The seed loader: loads the valid corpus, rejects the known-defective file, and
exits non-zero so CI notices — while still having loaded the good content."""

from __future__ import annotations

import pytest

from app.infrastructure.repository import ProblemRepository
from scripts.seed_exercises import SEED_DIR, main as seed_main, validate_files

pytestmark = pytest.mark.anyio


async def test_loads_six_rejects_water_and_exits_nonzero(session_factory, capsys):
    rc = await seed_main(session_factory=session_factory)
    assert rc != 0  # one file failed -> CI must notice

    out = capsys.readouterr().out
    assert "REJECTED" in out
    assert "science-g4-water" in out
    assert "total_steps" in out  # the reason is named, not just "invalid"
    assert "6 loaded, 1 rejected, 7 total" in out

    repo = ProblemRepository(session_factory)
    problems = await repo.list_problems()
    assert len(problems) == 6
    ids = {p.id for p in problems}
    assert "science-g4-water" not in ids
    assert "math-g4-apples" in ids


async def test_reseeding_is_idempotent(session_factory):
    await seed_main(session_factory=session_factory)
    await seed_main(session_factory=session_factory)  # upsert, not duplicate
    repo = ProblemRepository(session_factory)
    problems = await repo.list_problems()
    assert len(problems) == 6
    apples = await repo.get_problem("math-g4-apples")
    assert len(apples.steps) == 4  # steps replaced, not accumulated


def test_only_the_known_defect_fails_validation():
    results = validate_files(SEED_DIR)
    assert len(results) == 7
    failed = [r.file for r in results if not r.ok]
    assert failed == ["science-g4-water.yaml"]
