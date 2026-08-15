"""Service-local view of the shared contract.

The Pydantic contract lives in ``dal.schemas`` and is canonical — this module only
re-exports the pieces content_service uses, plus bilingual error strings for the
public API. Do not define problem shapes here (.claude/contracts.md section 2).
"""

from __future__ import annotations

from dal.schemas import (
    HomeworkProblem,
    PublicHomeworkProblem,
    PublicStepItem,
    StepItem,
    Subject,
)

__all__ = [
    "HomeworkProblem",
    "PublicHomeworkProblem",
    "PublicStepItem",
    "StepItem",
    "Subject",
    "problem_not_found_detail",
]


def problem_not_found_detail(problem_id: str) -> dict[str, str]:
    """Structured, bilingual 404 body — a child never sees a bare English error
    (.claude/claude.md section 5)."""
    return {
        "error": "problem_not_found",
        "problem_id": problem_id,
        "message_khmer": "រកមិនឃើញលំហាត់នេះទេ។ សូមព្យាយាមលំហាត់ផ្សេងទៀត!",
        "message_eng": "We could not find that problem. Let's try another one!",
    }
