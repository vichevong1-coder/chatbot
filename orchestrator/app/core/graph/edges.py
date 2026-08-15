"""Routing functions for the Phase-1 graph (architecture.md §2).

    input_normalizer ──(greeting)──▶ END          canned reply, zero services
            │
            ▼
       safety_gate ──(unsafe)──▶ END              refusal response
            │
          (safe)
            ▼
      intent_router ──▶ solve | explain
            solve ──(unparseable)──▶ explain ──▶ END
"""

from __future__ import annotations

from langgraph.graph import END

from app.core.graph.state import GraphState


def after_input_normalizer(state: GraphState) -> str:
    """Bare greetings skip everything — safe by exact-match construction."""
    if state.get("intent") == "greeting":
        return END
    return "safety_gate"


def after_safety_gate(state: GraphState) -> str:
    if state.get("is_safety_refusal"):
        return END
    return "intent_router"


def after_intent_router(state: GraphState) -> str:
    return "solve" if state.get("intent") == "solve" else "explain"


def after_solve(state: GraphState) -> str:
    """Solver 422 / outage resets intent to explain — fall through, don't fail."""
    if state.get("intent") == "explain":
        return "explain"
    return END
