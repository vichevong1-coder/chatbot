"""Age gate for generated OUTPUT — ages 6–12, stricter than the input filter.

Everything the base content filter blocks stays blocked; on top of that,
generated text must also be free of language a tutor should never use with a
child: insults, profanity-adjacent words, romance, gambling. Pure logic,
no FastAPI imports — reuses the content filter's rule machinery.
"""

from __future__ import annotations

from . import content_filter
from .content_filter import AGE_INAPPROPRIATE, Rule, Verdict

# Stricter, output-only rules. These would be over-blocking for a child's
# input (a frustrated "this is stupid" should not trigger a safety refusal),
# but a tutor's generated reply must never contain them.
STRICT_OUTPUT_RULES: tuple[Rule, ...] = (
    Rule(
        category=AGE_INAPPROPRIATE,
        patterns=(
            r"\bstupid\b",
            r"\bidiot\b",
            r"\bdumb\b",
            r"\bshut up\b",
            r"\bdamn\b",
            r"\bhell\b",
            r"\bgambl\w+\b",
            r"\bcasino\b",
            r"\bdating\b",
            r"\bboyfriend\b",
            r"\bgirlfriend\b",
            r"\bkiss(?:es|ed|ing)?\b",
        ),
        khmer=(
            "ល្ងង់",  # stupid
            "ឆ្កួត",  # crazy (as an insult)
            "ល្បែងស៊ីសង",  # gambling
            "សង្សារ",  # boyfriend/girlfriend
            "ថើប",  # kiss
        ),
    ),
)

# Base categories first so e.g. self-harm keeps its gentler refusal.
OUTPUT_RULES: tuple[Rule, ...] = content_filter.BASE_RULES + STRICT_OUTPUT_RULES


def screen_output(text: str) -> Verdict:
    """Screen generated text before it reaches the child."""
    return content_filter.check(text, rules=OUTPUT_RULES)
