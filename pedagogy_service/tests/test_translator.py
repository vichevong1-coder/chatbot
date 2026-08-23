"""Unit tests for TranslatorService and POST /translate."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dal.llm_client import LlmResult
from dal.schemas.enums import Language

from app.core.translator import TranslatorService
from app.main import create_app


class FakeLlmClient:
    def __init__(self, reply: str = "សួស្តី ពិភពលោក"):
        self.reply = reply
        self.calls: list[tuple[str, str, str | None]] = []

    async def generate(
        self,
        prompt: str,
        *,
        language: Language = Language.KHMER,
        system_instruction: str | None = None,
    ) -> LlmResult:
        self.calls.append((prompt, language.value, system_instruction))
        return LlmResult(
            text=self.reply,
            from_fallback=False,
            prompt_tokens=10,
            output_tokens=5,
        )


@pytest.mark.anyio
async def test_translator_service_english_to_khmer():
    fake_llm = FakeLlmClient(reply="តើអ្វីជាការរស្មីសំយោគ?")
    translator = TranslatorService(llm_client=fake_llm)  # type: ignore

    res = await translator.translate("What is photosynthesis?", target_language=Language.KHMER)
    assert res["translated_text"] == "តើអ្វីជាការរស្មីសំយោគ?"
    assert res["target_language"] == "km"
    assert len(fake_llm.calls) == 1
    assert "Khmer script" in fake_llm.calls[0][2]


@pytest.mark.anyio
async def test_translator_service_khmer_to_english():
    fake_llm = FakeLlmClient(reply="What is photosynthesis?")
    translator = TranslatorService(llm_client=fake_llm)  # type: ignore

    res = await translator.translate("តើអ្វីជាការរស្មីសំយោគ?", target_language=Language.ENGLISH)
    assert res["translated_text"] == "What is photosynthesis?"
    assert res["target_language"] == "en"
    assert len(fake_llm.calls) == 1
    assert "English" in fake_llm.calls[0][2]


def test_translate_endpoint():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/translate",
        json={"text": "What is photosynthesis?", "target_language": "km"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "translated_text" in data
    assert data["target_language"] == "km"
