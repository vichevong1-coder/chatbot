"""Cheap non-LLM shortcuts (architecture.md §2).

Rationale recorded there: an exact numeric match does not need a model call, and a
greeting needs neither a model nor the safety service — thirty children saying
"សួស្តី" every morning must cost zero tokens. Pure functions, no FastAPI, no I/O.
"""

from __future__ import annotations

import re

# Khmer numerals ០-៩ → ASCII, plus the operator glyphs Cambodian schoolbooks use.
# Same idea as solver_service's normalizer — deliberately NOT imported across
# services (claude.md §5: services never import each other).
_KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"
_KHMER_TO_ASCII = {ord(k): str(i) for i, k in enumerate(_KHMER_DIGITS)}
_OPERATOR_ALIASES = {ord("×"): "*", ord("÷"): "/", ord("−"): "-"}

_WHITESPACE_RE = re.compile(r"\s+")


def normalize(prompt: str) -> str:
    """Trim, map Khmer numerals/operator glyphs to ASCII, collapse whitespace.

    Used for downstream math detection only — the original prompt is kept for
    display and the transcript.
    """
    text = prompt.translate(_KHMER_TO_ASCII).translate(_OPERATOR_ALIASES)
    return _WHITESPACE_RE.sub(" ", text).strip()


# Bare arithmetic: digits/operators/parens/decimal points, optionally the
# "N% of X" percentage form the solver understands. Mirrors solver_service's
# token vocabulary without importing it.
_ARITHMETIC_RE = re.compile(r"^(?:\d+(?:\.\d+)?|of\b|[+\-*/()%]|\s)+$", re.IGNORECASE)
_HAS_DIGIT_RE = re.compile(r"\d")
_HAS_OPERATOR_RE = re.compile(r"[+\-*/%]")


def is_bare_arithmetic(normalized_prompt: str) -> bool:
    """True when the prompt is pure arithmetic worth sending to solver_service.

    Requires at least one digit and one operator so a lone "5" (or empty text)
    goes to the tutor, not the calculator.
    """
    text = normalized_prompt.strip()
    return bool(
        text
        and _ARITHMETIC_RE.fullmatch(text)
        and _HAS_DIGIT_RE.search(text)
        and _HAS_OPERATOR_RE.search(text)
    )


# Exact-match greetings only: a canned reply must never swallow a real question
# like "hi, why do I multiply?". Punctuation and emoji are tolerated at the edges.
_GREETINGS = {"hello", "hi", "hey", "សួស្តី", "សួរស្តី", "ជំរាបសួរ", "hello tunsay", "hi tunsay"}
_EDGE_PUNCT_RE = re.compile(r"^[\s!?.,🐰👋😀-🙏]+|[\s!?.,🐰👋😀-🙏]+$")

GREETING_KHMER = "សួស្តី! ខ្ញុំឈ្មោះ ទន្សាយ! 🐰 តោះដោះស្រាយលំហាត់ជាមួយគ្នា! តើថ្ងៃនេះមានលំហាត់អ្វីដែរ?"
GREETING_ENG = "Hello! I'm Tunsay! 🐰 Let's solve your homework together! What are you working on today?"


def is_greeting(normalized_prompt: str) -> bool:
    """True only for a bare greeting — safe by construction, so it may skip
    the safety gate and the LLM entirely (zero tokens, zero service calls)."""
    text = _EDGE_PUNCT_RE.sub("", normalized_prompt.lower())
    return text in _GREETINGS

_HINT_KEYWORDS = {"hint", "clue", "give hint", "give a hint", "need a hint", "តម្រុយ", "សុំតម្រុយ", "សូមតម្រុយ", "ប្រាប់តម្រុយ"}

def is_hint_request(normalized_prompt: str) -> bool:
    """True when the prompt contains keywords explicitly asking for a hint."""
    text = normalized_prompt.lower()
    return any(keyword in text for keyword in _HINT_KEYWORDS)


_RECOMMEND_KEYWORDS = {
    "recommend",
    "next problem",
    "next exercise",
    "what should i do next",
    "suggest a problem",
    "suggest next",
    "another problem",
    "practice next",
    "លំហាត់បន្ទាប់",
    "លំហាត់ថ្មី",
    "ណែនាំលំហាត់",
    "សូមណែនាំ",
    "លំហាត់ផ្សេងទៀត",
    "តើគួរធ្វើលំហាត់អ្វីបន្ទាប់",
}


def is_recommend_request(normalized_prompt: str) -> bool:
    """True when the prompt asks for a next problem recommendation."""
    text = normalized_prompt.lower()
    return any(keyword in text for keyword in _RECOMMEND_KEYWORDS)


_CLARIFY_KEYWORDS = {
    "?",
    "??",
    "???",
    "what",
    "why",
    "how",
    "help",
    "math",
    "science",
    "english",
    "homework",
    "exercise",
    "lesson",
    "problem",
    "question",
    "លំហាត់",
    "គណិត",
    "គណិតវិទ្យា",
    "ជួយ",
    "ជួយផង",
    "មេរៀន",
    "សំណួរ",
    "វិទ្យាសាស្ត្រ",
    "អង់គ្លេស",
}


def is_clarify_request(normalized_prompt: str) -> bool:
    """True when the prompt is ultra-short, vague, or empty and needs clarification."""
    text = normalized_prompt.strip().lower()
    if not text:
        return True
    clean = _EDGE_PUNCT_RE.sub("", text)
    if not clean:
        return True
    return clean in _CLARIFY_KEYWORDS or text in _CLARIFY_KEYWORDS


