"""The state carried through the orchestrator graph (architecture.md §2).

There is deliberately NO ``role`` field — every account is a student, and ``mode``
is the per-session student/parent toggle (contracts.md §4).
"""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    # Identity / request context (auth-aware from the first commit — plan.md P1.7)
    student_id: str
    session_id: str
    language: str  # "km" | "en"
    mode: str  # "student" | "parent" — a toggle, not a role
    problem_id: str | None
    active_step_index: int | None

    # Input
    prompt: str  # as the child typed it — kept for display / transcript
    normalized_prompt: str  # Khmer numerals → ASCII, whitespace collapsed
    transcript: list[dict[str, Any]]  # dal ChatMessage dicts, prior turns

    # Routing
    intent: str  # "greeting" | "solve" | "explain" | "hint"
    hint_level: int  # 0-3, tracks progressive hint escalation

    # Outward-facing result (maps straight onto dal ChatResponse)
    text_khmer: str
    text_eng: str
    is_safety_refusal: bool
    is_parent_help: bool
    is_correct: bool
    misconception_code: str | None
    suggested_next: str | None
