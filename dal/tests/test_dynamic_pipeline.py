"""Unit tests for Grade-Adaptive Pure Prompt Pipeline and 3-Tier Fallback."""

import asyncio
from dal.llm_client import LlmClient, build_socratic_fallback
from dal.schemas.enums import Language


def test_pure_prompt_socratic_fallback_unseen_questions():
    """Verify build_socratic_fallback uses pure prompt templates for unseen topics across grade bands."""
    # Grade 1 English concept
    res_g1 = build_socratic_fallback(
        prompt="Why do birds fly south in the winter?",
        language=Language.ENGLISH,
        grade=1,
    )
    assert "Step 1:" in res_g1
    assert res_g1.count("?") == 1

    # Grade 3 Biology concept
    res_g3 = build_socratic_fallback(
        prompt="How do sunflowers turn towards the sun?",
        language=Language.ENGLISH,
        grade=3,
    )
    assert "Step 1:" in res_g3
    assert res_g3.count("?") == 1

    # Grade 8 Physics concept
    res_g8 = build_socratic_fallback(
        prompt="What happens to the resistance when copper wire length doubles?",
        language=Language.ENGLISH,
        grade=8,
    )
    assert "Step 1:" in res_g8
    assert res_g8.count("?") == 1

    # Grade 11 Math concept
    res_g11 = build_socratic_fallback(
        prompt="Find the derivative of f(x) = x^3 + 4x.",
        language=Language.ENGLISH,
        grade=11,
    )
    assert "Step 1:" in res_g11
    assert res_g11.count("?") == 1


def test_three_tier_fallback_execution():
    """Verify LlmClient degrades seamlessly to Tier 3 pure prompt template fallback when no API key is set."""
    client = LlmClient(api_key=None)
    result = asyncio.run(
        client.generate(
            "Explain why rainwater is naturally acidic.",
            language=Language.ENGLISH,
        )
    )
    assert result.from_fallback is True
    assert "Step 1:" in result.text
    assert result.text.count("?") == 1
