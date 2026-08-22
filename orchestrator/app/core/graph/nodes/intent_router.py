"""Node 3 — classify the (safe) prompt. Pure heuristics, NO LLM.

Phase 1 knows two destinations: bare arithmetic goes to solver_service, anything
else goes to pedagogy_service. Greetings never reach this node — the normalizer
already short-circuited them (architecture.md §2 heuristics rationale).
"""

from __future__ import annotations

from app.core import heuristics
from app.core.graph.state import GraphState


async def intent_router(state: GraphState) -> dict:
    current_intent = state.get("intent")
    if current_intent in ("check_answer", "greeting"):
        return {}
    normalized = state.get("normalized_prompt", "")
    if heuristics.is_hint_request(normalized):
        return {"intent": "hint"}
    if heuristics.is_recommend_request(normalized):
        return {"intent": "recommend_next"}
    if heuristics.is_bare_arithmetic(normalized):
        return {"intent": "solve"}
    if heuristics.is_clarify_request(normalized):
        return {"intent": "clarify"}
    return {"intent": "explain"}
