"""Node 1 — unify the input into one normalized prompt.

Trims, maps Khmer numerals ០-៩ (and schoolbook glyphs ×÷−) to ASCII for
downstream math detection, and collapses whitespace. The ORIGINAL prompt is kept
in state for display and the transcript.

Also short-circuits bare greetings here, before the safety gate: a greeting only
matches by exact whitelist (heuristics.is_greeting), so it is safe by
construction and costs zero service calls and zero tokens — the cheap non-LLM
shortcut rationale of architecture.md §2 (heuristics.py).
"""

from __future__ import annotations

from app.core import heuristics
from app.core.graph.state import GraphState


async def input_normalizer(state: GraphState) -> dict:
    normalized = heuristics.normalize(state.get("prompt", ""))
    update: dict = {"normalized_prompt": normalized}

    if heuristics.is_greeting(normalized):
        # Canned bilingual pair, filled per the single-language rule
        # (contracts.md §3): requested language populated, other side "".
        is_khmer = state.get("language", "km") == "km"
        update.update(
            intent="greeting",
            text_khmer=heuristics.GREETING_KHMER if is_khmer else "",
            text_eng="" if is_khmer else heuristics.GREETING_ENG,
            is_safety_refusal=False,
            is_parent_help=False,
        )
    return update
