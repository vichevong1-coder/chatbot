"""Node 2 — call safety_service BEFORE spending a token (claude.md §4).

Fail-closed policy: if the safety service is down, unchecked text must never
reach the LLM — but the failure is soft. The child gets the generic bilingual
refusal (Tunsay-voiced, per language), never an HTTP 500.
"""

from __future__ import annotations

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients, ServiceUnavailable

# Generic refusal used when safety_service itself is unreachable. Authored pair;
# the requested language side is filled per the single-language rule.
GENERIC_REFUSAL_KHMER = (
    "សុំទោសណា! ទន្សាយមិនអាចឆ្លើយសំណួរនេះឥឡូវនេះទេ។ សូមព្យាយាមម្តងទៀតបន្តិចទៀត! 🐰"
)
GENERIC_REFUSAL_ENG = (
    "Sorry! Tunsay can't answer that right now. Please try again in a moment! 🐰"
)


def _single_language(khmer: str, eng: str, language: str) -> dict:
    if language == "km":
        return {"text_khmer": khmer, "text_eng": ""}
    return {"text_khmer": "", "text_eng": eng}


async def safety_gate(state: GraphState, clients: ServiceClients) -> dict:
    language = state.get("language", "km")
    try:
        verdict = await clients.safety.check(
            state.get("normalized_prompt", ""), language, direction="input"
        )
    except ServiceUnavailable:
        # Fail CLOSED, softly: refuse rather than let unchecked text through.
        return {
            "is_safety_refusal": True,
            **_single_language(GENERIC_REFUSAL_KHMER, GENERIC_REFUSAL_ENG, language),
        }

    if verdict.get("is_safe", False):
        return {"is_safety_refusal": False}

    return {
        "is_safety_refusal": True,
        **_single_language(
            verdict.get("refusal_khmer") or GENERIC_REFUSAL_KHMER,
            verdict.get("refusal_eng") or GENERIC_REFUSAL_ENG,
            language,
        ),
    }
