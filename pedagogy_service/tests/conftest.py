"""Make `app` importable when pytest runs from the repo root, plus shared fakes."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from dal.llm_client import LlmClient  # noqa: E402

from app.core.explanation_generator import ExplanationGenerator  # noqa: E402


class FakeCall:
    """Injectable stand-in for the Gemini SDK call: records inputs, returns text."""

    def __init__(self, text: str = "គិតមើលជំហានទីមួយ! 🐰") -> None:
        self.text = text
        self.calls: list[dict] = []

    async def __call__(self, *, model: str, prompt: str, system_instruction: str | None):
        self.calls.append(
            {"model": model, "prompt": prompt, "system_instruction": system_instruction}
        )
        return SimpleNamespace(
            text=self.text,
            usage_metadata=SimpleNamespace(
                prompt_token_count=11, candidates_token_count=7, total_token_count=18
            ),
        )


@pytest.fixture
def fake_call() -> FakeCall:
    return FakeCall()


@pytest.fixture
def generator(fake_call: FakeCall) -> ExplanationGenerator:
    """Generator whose LlmClient uses the fake call — no SDK, no network."""
    client = LlmClient(api_key="test-key", call=fake_call)
    return ExplanationGenerator(llm_client=client)


@pytest.fixture
def fallback_generator() -> ExplanationGenerator:
    """Generator with no usable API key: LlmClient short-circuits to fallback."""

    async def explode(**_kwargs):  # pragma: no cover - must never run
        raise AssertionError("SDK call attempted despite missing API key")

    client = LlmClient(api_key="MY_GEMINI_API_KEY", call=explode)
    return ExplanationGenerator(llm_client=client)
