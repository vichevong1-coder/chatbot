"""P1.2 verify — dal.llm_client with the Gemini call mocked, plus client factory smoke.

No live Gemini, Postgres or Redis is required. Coroutines are driven with
``asyncio.run`` so no async pytest plugin is needed.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from dal.llm_client import FALLBACK_TEXT, DEFAULT_MODEL, LlmClient, LlmResult
from dal.schemas import Language

KM_FALLBACK = "មិនអីទេ! តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នាណា។ 🐰"
EN_FALLBACK = "No problem! Let's look at this step together. 🐰"


class Transient503(Exception):
    """Duck-typed 503, the shape genai's APIError exposes via ``.code``."""

    code = 503


class InvalidKey(Exception):
    """Non-transient auth-style failure (400 INVALID_ARGUMENT / bad API key)."""

    code = 400


def _response(text="Let's count the apples together!", *, usage=True):
    usage_metadata = (
        SimpleNamespace(prompt_token_count=12, candidates_token_count=34, total_token_count=46)
        if usage
        else None
    )
    return SimpleNamespace(text=text, usage_metadata=usage_metadata)


class FakeCall:
    """Injectable stand-in for the SDK call: raises scripted errors, then answers."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    async def __call__(self, *, model, prompt, system_instruction):
        self.calls.append({"model": model, "prompt": prompt, "system": system_instruction})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class RecordingSleep:
    def __init__(self):
        self.delays = []

    async def __call__(self, seconds):
        self.delays.append(seconds)


def make_client(outcomes, **kwargs):
    call = FakeCall(outcomes)
    sleep = RecordingSleep()
    kwargs.setdefault("api_key", "test-key-not-a-placeholder")
    kwargs.setdefault("backoff_base_seconds", 0.5)
    client = LlmClient(call=call, sleep=sleep, **kwargs)
    return client, call, sleep


# -- success ---------------------------------------------------------------------------


def test_success_first_attempt_returns_text_and_tokens():
    client, call, sleep = make_client([_response()])
    result = asyncio.run(client.generate("why do I multiply?", language=Language.KHMER))

    assert isinstance(result, LlmResult)
    assert result.text == "Let's count the apples together!"
    assert result.from_fallback is False
    assert result.attempts == 1
    assert (result.prompt_tokens, result.output_tokens, result.total_tokens) == (12, 34, 46)
    assert len(call.calls) == 1
    assert sleep.delays == []  # no retry, no backoff


def test_success_passes_model_and_system_instruction_through():
    client, call, _ = make_client([_response()], model="my-model")
    asyncio.run(
        client.generate("q", language=Language.ENGLISH, system_instruction="be a rabbit")
    )
    assert call.calls[0]["model"] == "my-model"
    assert call.calls[0]["system"] == "be a rabbit"


def test_missing_usage_metadata_leaves_token_fields_none():
    client, _, _ = make_client([_response(usage=False)])
    result = asyncio.run(client.generate("q", language=Language.KHMER))
    assert result.from_fallback is False
    assert result.prompt_tokens is None
    assert result.output_tokens is None
    assert result.total_tokens is None


# -- retry -----------------------------------------------------------------------------


def test_two_503s_then_success_uses_three_attempts():
    client, call, sleep = make_client([Transient503(), Transient503(), _response("third time")])
    result = asyncio.run(client.generate("q", language=Language.KHMER))

    assert result.text == "third time"
    assert result.from_fallback is False
    assert result.attempts == 3
    assert len(call.calls) == 3
    assert len(sleep.delays) == 2


def test_backoff_delays_increase_exponentially():
    client, _, sleep = make_client(
        [Transient503(), Transient503(), _response()], backoff_base_seconds=0.5
    )
    asyncio.run(client.generate("q", language=Language.KHMER))
    assert sleep.delays == [0.5, 1.0]
    assert sleep.delays == sorted(sleep.delays)
    assert sleep.delays[1] > sleep.delays[0]


def test_timeout_is_transient_and_retried():
    async def hang(*, model, prompt, system_instruction):
        await asyncio.sleep(60)

    calls = {"n": 0}

    async def call(*, model, prompt, system_instruction):
        calls["n"] += 1
        if calls["n"] == 1:
            return await hang(model=model, prompt=prompt, system_instruction=system_instruction)
        return _response("recovered")

    sleep = RecordingSleep()
    client = LlmClient(
        api_key="k", call=call, sleep=sleep, timeout_seconds=0.01, max_attempts=3
    )
    result = asyncio.run(client.generate("q", language=Language.ENGLISH))
    assert result.text == "recovered"
    assert result.attempts == 2


# -- fallback: never raise -------------------------------------------------------------


def test_all_attempts_fail_returns_khmer_fallback_no_exception():
    client, call, _ = make_client([Transient503(), Transient503(), Transient503()])
    result = asyncio.run(client.generate("q", language=Language.KHMER))

    assert result.from_fallback is True
    assert result.text == KM_FALLBACK
    assert result.attempts == 3
    assert len(call.calls) == 3


def test_all_attempts_fail_returns_english_fallback():
    client, _, _ = make_client([Transient503(), Transient503(), Transient503()])
    result = asyncio.run(client.generate("q", language=Language.ENGLISH))
    assert result.from_fallback is True
    assert result.text == EN_FALLBACK


def test_fallback_strings_match_server_ts():
    assert FALLBACK_TEXT[Language.KHMER] == KM_FALLBACK
    assert FALLBACK_TEXT[Language.ENGLISH] == EN_FALLBACK


def test_totally_unexpected_exception_still_returns_fallback():
    client, _, _ = make_client([RuntimeError("boom"), RuntimeError("boom"), RuntimeError("boom")])
    result = asyncio.run(client.generate("q", language=Language.KHMER))
    assert result.from_fallback is True
    assert result.text == KM_FALLBACK


# -- key handling ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "key", [None, "", "  ", "MY_GEMINI_API_KEY", "replace-with-your-gemini-api-key"]
)
def test_missing_or_placeholder_key_short_circuits_with_zero_sdk_calls(key, monkeypatch):
    if key is None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEMINI_API_KEY", key)
    call = FakeCall([_response()])
    client = LlmClient(call=call, sleep=RecordingSleep())

    result = asyncio.run(client.generate("q", language=Language.KHMER))
    assert result.from_fallback is True
    assert result.text == KM_FALLBACK
    assert result.attempts == 0
    assert call.calls == []  # the SDK is never touched


# -- non-transient errors --------------------------------------------------------------


def test_non_transient_error_goes_straight_to_fallback_without_retries():
    client, call, sleep = make_client([InvalidKey(), _response("should never be reached")])
    result = asyncio.run(client.generate("q", language=Language.ENGLISH))

    assert result.from_fallback is True
    assert result.text == EN_FALLBACK
    assert result.attempts == 1
    assert len(call.calls) == 1  # no retry burned on an unfixable error
    assert sleep.delays == []


def test_genai_server_error_is_transient_and_client_error_is_not():
    from google.genai import errors as genai_errors

    from dal.llm_client import _is_transient

    import unittest.mock
    mock_resp = unittest.mock.Mock()
    mock_resp.body_segments = [{"error": {"message": "unavailable"}}]
    mock_resp_client = unittest.mock.Mock()
    mock_resp_client.body_segments = [{"error": {"message": "bad key"}}]

    server = genai_errors.ServerError(503, mock_resp)
    client_err = genai_errors.ClientError(401, mock_resp_client)
    assert _is_transient(server) is True
    assert _is_transient(client_err) is False
    assert _is_transient(asyncio.TimeoutError()) is True
    assert _is_transient(ConnectionError()) is True


# -- config ----------------------------------------------------------------------------


def test_default_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-x-test")
    fake = FakeCall([_response()])
    llm = LlmClient(api_key="k", call=fake, sleep=RecordingSleep())
    asyncio.run(llm.generate("q", language=Language.KHMER))
    assert fake.calls[0]["model"] == "gemini-x-test"

    monkeypatch.delenv("GEMINI_MODEL")
    fake2 = FakeCall([_response()])
    llm2 = LlmClient(api_key="k", call=fake2, sleep=RecordingSleep())
    asyncio.run(llm2.generate("q", language=Language.KHMER))
    assert fake2.calls[0]["model"] == DEFAULT_MODEL  # unverified id, kept configurable


# -- clients smoke: build from env URLs without connecting -----------------------------


def test_postgres_factory_builds_engine_from_env(monkeypatch):
    from dal.clients import postgres

    postgres.reset()
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://tunsay:pw@localhost:5432/tunsay_test"
    )
    engine = postgres.get_engine()
    assert engine.url.drivername == "postgresql+psycopg"  # async driver rewrite
    assert postgres.get_engine() is engine  # cached
    factory = postgres.get_session_factory()
    assert factory is postgres.get_session_factory()
    postgres.reset()


def test_redis_factory_builds_client_from_env(monkeypatch):
    from dal.clients import redis as redis_client

    redis_client.reset()
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis_client.get_redis()
    assert redis_client.get_redis() is client  # cached
    kwargs = client.connection_pool.connection_kwargs
    assert kwargs["port"] == 6379
    assert kwargs["decode_responses"] is True
    redis_client.reset()


def test_clients_package_exports():
    import dal.clients as clients

    assert callable(clients.get_engine)
    assert callable(clients.get_session_factory)
    assert callable(clients.get_redis)


def test_ollama_provider_flow(monkeypatch):
    import unittest.mock
    import httpx
    from dal.llm_client import LlmClient, Language

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    monkeypatch.setenv("OLLAMA_URL", "http://fake-ollama:11434")

    mock_response = unittest.mock.Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Socratic hint from Llama!"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }
    mock_response.raise_for_status = unittest.mock.Mock()

    async def fake_post(self, url, **kwargs):
        assert url == "http://fake-ollama:11434/v1/chat/completions"
        payload = kwargs.get("json", {})
        assert payload["model"] == "llama3.2:3b"
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "system instruction"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "prompt instruction"
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = LlmClient()
    result = asyncio.run(client.generate(
        "prompt instruction",
        language=Language.ENGLISH,
        system_instruction="system instruction"
    ))

    assert result.from_fallback is False
    assert result.text == "Socratic hint from Llama!"
    assert result.prompt_tokens == 10
    assert result.output_tokens == 15
    assert result.total_tokens == 25
