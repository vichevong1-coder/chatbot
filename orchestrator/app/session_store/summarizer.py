"""Deterministic chat transcript summarizer to prevent context window overflow."""

from __future__ import annotations

from typing import Any


def summarize_transcript(
    transcript: list[dict[str, Any]],
    language: str = "km",
) -> tuple[list[dict[str, Any]], str | None]:
    """Condenses long transcripts.

    Returns a tuple of:
    - The trimmed transcript list (keeping the last 4 messages in full).
    - An optional text summary string of the older messages to inject into the context.
    """
    if len(transcript) <= 6:
        return transcript, None

    # Keep the last 4 messages in full
    trimmed_transcript = transcript[-4:]
    older_messages = transcript[:-4]

    # Generate a summary statement of the older turns
    user_turns = 0
    assistant_turns = 0
    safety_refusals = 0

    for msg in older_messages:
        sender = msg.get("sender")
        if sender == "user":
            user_turns += 1
        elif sender == "sayo":
            assistant_turns += 1
            if msg.get("is_safety_refusal"):
                safety_refusals += 1

    if language == "km":
        summary = f"ការសន្ទនាមុន៖ សិស្សសួរ {user_turns} ដង, ជំនួយការឆ្លើយ {assistant_turns} ដង"
        if safety_refusals > 0:
            summary += f" (រារាំងដោយសុវត្ថិភាព {safety_refusals} ដង)"
    else:
        summary = f"Earlier conversation: student asked {user_turns} times, assistant replied {assistant_turns} times"
        if safety_refusals > 0:
            summary += f" ({safety_refusals} safety warnings)"

    return trimmed_transcript, summary
