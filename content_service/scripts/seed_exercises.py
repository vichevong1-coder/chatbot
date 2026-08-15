"""Load seed_data/*.yaml into the problems/steps tables.

Every file is validated through ``dal.schemas.HomeworkProblem`` — the same rules that
gate admin ingest (bilingual fields both populated, mcq steps carry options,
``total_steps == len(steps)``). Valid problems are upserted; invalid ones are SKIPPED
with a per-file report and the script exits non-zero so CI notices, while the good
content is still loaded.

Expected today: 6 loaded, 1 rejected — ``science-g4-water`` declares ``total_steps: 3``
on a 2-step problem, a known corpus defect (.claude/contracts.md section 6). Do not
"fix" the YAML; fix the frontend source and re-transcode.

Run from the service directory (or via compose):

    python scripts/seed_exercises.py
    docker compose run --rm content_service python scripts/seed_exercises.py
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

# The script lives beside `app/`, not inside it — make the service dir importable so
# `python scripts/seed_exercises.py` works without an install step.
SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

from dal.models import Base  # noqa: E402
from dal.schemas import HomeworkProblem  # noqa: E402

from app.infrastructure.repository import ProblemRepository  # noqa: E402

SEED_DIR = SERVICE_DIR / "seed_data"


@dataclass
class SeedResult:
    file: str
    problem: HomeworkProblem | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.problem is not None


def _first_error_line(exc: Exception) -> str:
    """One human-readable line per rejected file, not a pydantic wall of text."""
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first["loc"]) or "<root>"
        return f"{loc}: {first['msg']}"
    return f"{type(exc).__name__}: {exc}"


def validate_files(seed_dir: Path) -> list[SeedResult]:
    results: list[SeedResult] = []
    for path in sorted(seed_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            results.append(SeedResult(path.name, HomeworkProblem.model_validate(raw), None))
        except Exception as exc:  # noqa: BLE001 — every failure becomes a report row
            results.append(SeedResult(path.name, None, _first_error_line(exc)))
    return results


def print_summary(results: list[SeedResult]) -> None:
    print(f"{'id':<24} {'grade':>5} {'subject':<8} {'steps':>5}  status")
    print("-" * 78)
    for r in results:
        if r.ok:
            p = r.problem
            print(f"{p.id:<24} {p.grade:>5} {p.subject.value:<8} {len(p.steps):>5}  OK")
        else:
            slug = r.file.removesuffix(".yaml")
            print(f"{slug:<24} {'-':>5} {'-':<8} {'-':>5}  REJECTED — {r.error}")
    loaded = sum(r.ok for r in results)
    print("-" * 78)
    print(f"{loaded} loaded, {len(results) - loaded} rejected, {len(results)} total")


async def main(
    seed_dir: Path = SEED_DIR,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> int:
    """Validate, load, report. Returns the process exit code: 0 only if every file
    passed. ``session_factory`` is injectable so tests seed into SQLite."""
    create_tables = session_factory is None
    repo = ProblemRepository(session_factory)

    if create_tables:
        # First run against a fresh database: no alembic migrations exist yet, so the
        # seeder owns table creation (idempotent checkfirst).
        engine = repo.session_factory.kw["bind"]
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    results = validate_files(seed_dir)
    for r in results:
        if r.ok:
            await repo.upsert_problem(r.problem)

    print_summary(results)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
