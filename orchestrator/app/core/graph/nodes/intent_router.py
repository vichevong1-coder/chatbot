"""Node 3 — classify the (safe) prompt. Pure heuristics, NO LLM.

Phase 1 knows two destinations: bare arithmetic goes to solver_service, anything
else goes to pedagogy_service. Greetings never reach this node — the normalizer
already short-circuited them (architecture.md §2 heuristics rationale).
"""

from __future__ import annotations

from app.core import heuristics
from app.core.graph.state import GraphState


async def intent_router(state: GraphState) -> dict:
    if heuristics.is_bare_arithmetic(state.get("normalized_prompt", "")):
        return {"intent": "solve"}
    return {"intent": "explain"}
