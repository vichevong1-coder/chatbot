"""Node: clarify asks a friendly question when the student's input is ambiguous.

Bilingual Tunsay voice asking what homework problem or topic they would like help with.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients

CLARIFY_STUDENT_KHMER = (
    "តើប្អូនចង់ឱ្យទន្សាយជួយលើលំហាត់ ឬមេរៀនអ្វីដែរ? សូមប្រាប់ឈ្មោះលំហាត់ ឬប្រធានបទមកណា! 🐰"
)
CLARIFY_STUDENT_ENG = (
    "What homework problem or topic would you like help with? Please tell me the exercise or question! 🐰"
)

CLARIFY_PARENT_KHMER = (
    "តើលោកអ្នកចង់ឱ្យទន្សាយជួយពន្យល់ពីលំហាត់ ឬមេរៀនអ្វីសម្រាប់បង្រៀនកូនដែរ? 🐰"
)
CLARIFY_PARENT_ENG = (
    "What homework problem or topic would you like help explaining to your child? 🐰"
)


def _pick(khmer: str, eng: str, language: str) -> tuple[str, str]:
    if language == "km":
        return khmer, ""
    return "", eng


async def clarify(state: GraphState, clients: ServiceClients) -> dict[str, Any]:
    """Provide a friendly bilingual clarification question."""
    language = state.get("language", "km")
    mode = state.get("mode", "student")

    if mode == "parent":
        km_text = CLARIFY_PARENT_KHMER
        en_text = CLARIFY_PARENT_ENG
    else:
        km_text = CLARIFY_STUDENT_KHMER
        en_text = CLARIFY_STUDENT_ENG

    text_khmer, text_eng = _pick(km_text, en_text, language)

    return {
        "intent": "clarify",
        "text_khmer": text_khmer,
        "text_eng": text_eng,
        "is_parent_help": mode == "parent",
    }
