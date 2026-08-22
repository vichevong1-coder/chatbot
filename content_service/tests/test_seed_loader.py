"""The seed loader: loads the valid corpus and exits zero on clean seed."""

from __future__ import annotations

import pytest

from app.infrastructure.repository import ProblemRepository
from scripts.seed_exercises import SEED_DIR, main as seed_main, validate_files

pytestmark = pytest.mark.anyio


async def test_loads_all_nine_and_exits_zero(session_factory, capsys):
    rc = await seed_main(session_factory=session_factory)
    assert rc == 0

    out = capsys.readouterr().out
    assert "9 loaded, 0 rejected, 9 total" in out

    repo = ProblemRepository(session_factory)
    problems = await repo.list_problems()
    assert len(problems) == 9
    ids = {p.id for p in problems}
    assert "science-g4-water" in ids
    assert "math-g4-apples" in ids
    assert "math-g6-ratio" in ids
    assert "science-g6-ecosystems" in ids


async def test_reseeding_is_idempotent(session_factory):
    await seed_main(session_factory=session_factory)
    await seed_main(session_factory=session_factory)  # upsert, not duplicate
    repo = ProblemRepository(session_factory)
    problems = await repo.list_problems()
    assert len(problems) == 9
    apples = await repo.get_problem("math-g4-apples")
    assert len(apples.steps) == 4  # steps replaced, not accumulated


def test_only_the_known_defect_fails_validation():
    results = validate_files(SEED_DIR)
    assert len(results) == 9
    failed = [r.file for r in results if not r.ok]
    assert failed == []
