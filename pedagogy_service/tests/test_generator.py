"""Core tests for ExplanationGenerator: bands, prompt assembly, language sides."""

from __future__ import annotations

import asyncio

import pytest

from dal.llm_client import FALLBACK_TEXT
from dal.schemas.enums import Language, UserMode

from app.core.explanation_generator import BANDS, band_for_grade

# -- band table -------------------------------------------------------------------


def test_band_table_covers_grades_1_to_6():
    assert band_for_grade(2).name == "grade1_3"
    assert band_for_grade(5).name == "grade4_6"


def test_band_table_is_a_lookup_not_an_if_chain():
    # The plan requires a table; assert the table exists and maps files.
    assert {band.name: band.prompt_file for band in BANDS} == {
        "grade1_3": "explain_grade1_3.yaml",
        "grade4_6": "explain_grade4_6.yaml",
    }


@pytest.mark.parametrize("grade", [7, 8, 12])
def test_unmapped_grade_falls_back_to_nearest_band(grade: int):
    # 7-9 and 10-12 are reserved 0-byte stubs; until they're filled, the nearest
    # implemented band is grade4_6. No error for any structurally valid grade.
    assert band_for_grade(grade).name == "grade4_6"


# -- prompt assembly --------------------------------------------------------------


def test_system_instruction_ports_the_server_ts_voice(generator):
    text = generator.build_system_instruction(
        grade=5, language=Language.KHMER, mode=UserMode.STUDENT
    )
    assert "Tunsay (ទន្សាយ)" in text
    assert "friendly cartoon rabbit" in text
    assert "Westline Education Group (WEG)" in text
    assert "without giving direct answers immediately" in text
    assert "Never be judgmental" in text
    assert '"Let\'s solve it together"' in text


def test_grade_2_and_grade_5_select_different_bands(generator):
    g2 = generator.build_system_instruction(
        grade=2, language=Language.ENGLISH, mode=UserMode.STUDENT
    )
    g5 = generator.build_system_instruction(
        grade=5, language=Language.ENGLISH, mode=UserMode.STUDENT
    )
    assert "Grade 1–3" in g2 and "very short sentences" in g2
    assert "Grade 4–6" in g5 and "upper-primary" in g5
    assert g2 != g5


@pytest.mark.parametrize("grade", [8, 12])
def test_unmapped_grade_assembles_with_nearest_band(generator, grade: int):
    text = generator.build_system_instruction(
        grade=grade, language=Language.ENGLISH, mode=UserMode.STUDENT
    )
    assert "Grade 4–6" in text  # nearest band, no error


def test_language_instruction_km_ported_verbatim(generator):
    text = generator.build_system_instruction(
        grade=4, language=Language.KHMER, mode=UserMode.STUDENT
    )
    assert (
        "Always reply exclusively in clear, warm, encouraging Khmer language "
        "for primary students (Grades 1–6). Do not include any English "
        "translation in the response." in text
    )


def test_language_instruction_en_ported_verbatim(generator):
    text = generator.build_system_instruction(
        grade=4, language=Language.ENGLISH, mode=UserMode.STUDENT
    )
    assert (
        "Always reply exclusively in clear, warm, simple English language "
        "for primary students (Grades 1–6). Do not include any Khmer "
        "translation in the response." in text
    )


def test_student_mode_contains_never_reveal_instruction(generator):
    text = generator.build_system_instruction(
        grade=5, language=Language.KHMER, mode=UserMode.STUDENT
    )
    assert "Mode: student." in text
    assert "Never reveal the final answer" in text
    assert "Mode: parent." not in text


def test_parent_mode_contains_parent_block(generator):
    text = generator.build_system_instruction(
        grade=5, language=Language.KHMER, mode=UserMode.PARENT
    )
    assert "Mode: parent." in text
    assert "may reveal the final answer" in text
    assert "Never reveal the final answer" not in text


# -- generation -------------------------------------------------------------------


def test_km_request_fills_khmer_side_only(generator, fake_call):
    result = asyncio.run(generator.explain(
        prompt="ហេតុអ្វីខ្ញុំគុណ?", grade=4, language=Language.KHMER, mode=UserMode.STUDENT
    ))
    assert result["text_khmer"] == fake_call.text
    assert result["text_eng"] == ""
    assert result["from_fallback"] is False
    assert result["prompt_tokens"] == 11
    assert result["output_tokens"] == 7


def test_en_request_fills_english_side_only(fake_call, generator):
    fake_call.text = "Great question! Let's solve it together. 🐰"
    result = asyncio.run(generator.explain(
        prompt="why do I multiply?", grade=4, language=Language.ENGLISH, mode=UserMode.STUDENT
    ))
    assert result["text_eng"] == fake_call.text
    assert result["text_khmer"] == ""
    assert result["from_fallback"] is False


def test_context_rides_along_in_the_prompt(generator, fake_call):
    asyncio.run(generator.explain(
        prompt="why?",
        grade=4,
        language=Language.ENGLISH,
        mode=UserMode.STUDENT,
        context="Step 1: count the apples",
    ))
    sent = fake_call.calls[-1]["prompt"]
    assert "why?" in sent and "Context: Step 1: count the apples" in sent


def test_call_receives_assembled_system_instruction(generator, fake_call):
    asyncio.run(generator.explain(
        prompt="hi", grade=2, language=Language.ENGLISH, mode=UserMode.PARENT
    ))
    system = fake_call.calls[-1]["system_instruction"]
    assert "Tunsay (ទន្សាយ)" in system
    assert "very short sentences" in system  # grade1_3 band
    assert "Mode: parent." in system


def test_no_api_key_returns_bilingual_fallback_km(fallback_generator):
    result = asyncio.run(fallback_generator.explain(
        prompt="hello", grade=4, language=Language.KHMER, mode=UserMode.STUDENT
    ))
    assert result["from_fallback"] is True
    assert result["text_khmer"] == FALLBACK_TEXT[Language.KHMER]
    assert result["text_eng"] == ""
    assert result["prompt_tokens"] is None and result["output_tokens"] is None


def test_no_api_key_returns_bilingual_fallback_en(fallback_generator):
    result = asyncio.run(fallback_generator.explain(
        prompt="hello", grade=4, language=Language.ENGLISH, mode=UserMode.STUDENT
    ))
    assert result["from_fallback"] is True
    assert result["text_eng"] == FALLBACK_TEXT[Language.ENGLISH]
    assert result["text_khmer"] == ""
