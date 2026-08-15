"""Unit tests for the non-LLM shortcuts — pure functions, no app needed."""

from __future__ import annotations

from app.core import heuristics


def test_normalize_khmer_numerals_and_glyphs():
    assert heuristics.normalize("  ៥ × ៨  ") == "5 * 8"
    assert heuristics.normalize("១/២ + ១/៤") == "1/2 + 1/4"


def test_normalize_collapses_whitespace():
    assert heuristics.normalize("why   do\n I  multiply?") == "why do I multiply?"


def test_bare_arithmetic_detection():
    assert heuristics.is_bare_arithmetic("5*8")
    assert heuristics.is_bare_arithmetic("(1 + 2) / 3")
    assert heuristics.is_bare_arithmetic("25% of 80")
    assert not heuristics.is_bare_arithmetic("5")  # a lone number is not a sum
    assert not heuristics.is_bare_arithmetic("what is 5*8?")  # words → tutor
    assert not heuristics.is_bare_arithmetic("")


def test_greeting_detection_is_exact_match_only():
    assert heuristics.is_greeting("hello")
    assert heuristics.is_greeting("Hi!")
    assert heuristics.is_greeting("សួស្តី")
    assert not heuristics.is_greeting("hi, why do I multiply?")  # real question
    assert not heuristics.is_greeting("5*8")
