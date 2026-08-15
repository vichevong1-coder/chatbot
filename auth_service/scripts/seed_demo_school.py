"""Upsert the demo school so the P1.3 verify curl works.

TUNSAY-G4-DEMO is the code LoginView.tsx uses in its demo copy; /register 404s on an
unknown code, so the row must exist before the curl round-trip.

Also creates the ``schools`` and ``users`` tables if they are missing (checkfirst) —
Alembic migrations are not written yet, and only these two tables are auth_service's.

Run (inside compose, or anywhere DATABASE_URL points at the DB):

    python scripts/seed_demo_school.py
"""

from __future__ import annotations

import asyncio

from dal.clients.postgres import dispose, get_engine, get_session_factory
from dal.models.base import Base
from dal.models.user import School, User

DEMO = {
    "code": "TUNSAY-G4-DEMO",
    "name": "Primary Learning Campus",
    "class_name": "Class 4A",
    "grade": 4,
}


async def main() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[School.__table__, User.__table__], checkfirst=True
            )
        )

    factory = get_session_factory()
    async with factory() as session:
        school = await session.get(School, DEMO["code"])
        if school is None:
            session.add(School(**DEMO))
            action = "created"
        else:
            school.name = DEMO["name"]
            school.class_name = DEMO["class_name"]
            school.grade = DEMO["grade"]
            action = "updated"
        await session.commit()
    print(f"{action}: {DEMO['code']} (grade {DEMO['grade']}, {DEMO['class_name']})")
    await dispose()


if __name__ == "__main__":
    asyncio.run(main())
