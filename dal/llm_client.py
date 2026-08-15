"""Gemini wrapper: timeout, bounded retry with backoff, token accounting, and a
bilingual fallback on failure.

This is the only place in the backend that talks to the LLM. Two rules bind it:

- **Never propagate a raw exception toward a child.** ``generate()`` always returns an
  :class:`LlmResult`; on any failure it carries the Tunsay-voiced bilingual fallback
  (matching the strings ``frontend_tunsay/server.ts`` already uses) with
  ``from_fallback=True``.
- **Never log prompt or answer content** — this is children's data
  (.claude/claude.md section 5). Log lines carry only attempt counts, model ids and
  exception class names.

Google Gemini is the only LLM provider (.claude/claude.md section 4). The SDK is
``google-genai``; async calls go through ``client.aio.models.generate_content``.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, Protocol

import httpx
from google.genai import errors as genai_errors

from dal.schemas.base import TunsayModel
from dal.schemas.enums import Language

logger = logging.getLogger(__name__)

# NOTE: ``gemini-3.7-flash`` is inherited from frontend_tunsay/server.ts and is
# UNVERIFIED against Google's current model ids (.claude/claude.md section 4 /
# plan.md "Content, not code"). Keep it configurable via GEMINI_MODEL; do not
# "fix" the default here without confirming the real id first.
DEFAULT_MODEL_ENV = "GEMINI_MODEL"
DEFAULT_MODEL = "gemini-3.7-flash"

# Values of GEMINI_API_KEY that mean "no key configured". server.ts checks for
# 'MY_GEMINI_API_KEY'; .env.example ships 'replace-with-your-gemini-api-key'.
_PLACEHOLDER_KEYS = frozenset({"", "MY_GEMINI_API_KEY", "replace-with-your-gemini-api-key"})

# Same voice as the server.ts catch block — warm, never an error message.
FALLBACK_TEXT: dict[Language, str] = {
    Language.KHMER: "មិនអីទេ! តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នាណា។ 🐰",
    Language.ENGLISH: "No problem! Let's look at this step together. 🐰",
}

# HTTP-ish status codes worth retrying: timeouts, throttling, transient 5xx.
_TRANSIENT_STATUS = frozenset({408, 429, 500, 502, 503, 504})


class _GenerateCall(Protocol):
    def __call__(
        self, *, model: str, prompt: str, system_instruction: str | None
    ) -> Awaitable[Any]: ...


class LlmResult(TunsayModel):
    """Outcome of one :meth:`LlmClient.generate` call. Never an exception."""

    text: str
    from_fallback: bool = False
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    attempts: int = 0


def _is_transient(exc: BaseException) -> bool:
    """Should this failure be retried? Timeouts, connection drops, 5xx/429: yes.

    Auth errors, invalid arguments and other client-side 4xx: no — retrying an
    invalid API key just burns the backoff budget before the same fallback.
    """
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError)):
        return True
    if isinstance(exc, httpx.TransportError):  # DNS, connect, read/write failures
        return True
    if isinstance(exc, genai_errors.ServerError):  # 5xx from the API
        return True
    # genai APIError carries .code; duck-type it too so tests and other SDK error
    # shapes (status_code / status) are classified the same way.
    for attr in ("code", "status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value in _TRANSIENT_STATUS
    return False


class LlmClient:
    """Async Gemini client with per-attempt timeout, bounded retry and fallback.

    Parameters
    ----------
    api_key:
        Overrides ``GEMINI_API_KEY``. A missing or placeholder key short-circuits to
        the fallback without touching the SDK.
    model:
        Overrides ``GEMINI_MODEL`` (default :data:`DEFAULT_MODEL` — unverified id,
        see the note above).
    timeout_seconds:
        Per-attempt ceiling enforced with ``asyncio.wait_for``.
    max_attempts:
        Total tries for transient failures (not per-error).
    backoff_base_seconds:
        First retry delay; doubles each retry (exponential backoff).
    call:
        Injectable async callable ``(model=, prompt=, system_instruction=) -> response``
        so tests can stand in for the SDK without patching its internals. When omitted,
        a real ``google-genai`` client is built lazily on first use.
    sleep:
        Injectable awaitable sleep (defaults to ``asyncio.sleep``) so tests don't wait
        out the backoff.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
        max_attempts: int = 3,
        backoff_base_seconds: float = 1.0,
        call: _GenerateCall | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get(DEFAULT_MODEL_ENV, "").strip() or DEFAULT_MODEL
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max(1, max_attempts)
        self._backoff_base_seconds = backoff_base_seconds
        self._call = call
        self._sleep = sleep

    # -- configuration ------------------------------------------------------------

    def _effective_api_key(self) -> str | None:
        key = self._api_key if self._api_key is not None else os.environ.get("GEMINI_API_KEY")
        key = (key or "").strip()
        return None if key in _PLACEHOLDER_KEYS else key

    def _resolve_call(self) -> _GenerateCall:
        if self._call is None:
            # Imported lazily so a mocked client never needs the SDK wired up.
            from google import genai

            client = genai.Client(api_key=self._effective_api_key())

            async def _sdk_call(
                *, model: str, prompt: str, system_instruction: str | None
            ) -> Any:
                config = None
                if system_instruction is not None:
                    from google.genai import types

                    config = types.GenerateContentConfig(system_instruction=system_instruction)
                return await client.aio.models.generate_content(
                    model=model, contents=prompt, config=config
                )

            self._call = _sdk_call
        return self._call

    # -- results ------------------------------------------------------------------

    @staticmethod
    def _fallback(language: Language, attempts: int) -> LlmResult:
        return LlmResult(
            text=FALLBACK_TEXT.get(Language(language), FALLBACK_TEXT[Language.KHMER]),
            from_fallback=True,
            attempts=attempts,
        )

    @staticmethod
    def _result_from_response(response: Any, attempts: int) -> LlmResult | None:
        text = getattr(response, "text", None)
        if not text:
            return None
        usage = getattr(response, "usage_metadata", None)
        return LlmResult(
            text=text,
            from_fallback=False,
            prompt_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            total_tokens=getattr(usage, "total_token_count", None),
            attempts=attempts,
        )

    # -- the one public entry point ------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        language: Language,
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> LlmResult:
        """Generate a completion; on any failure return the bilingual fallback.

        This method never raises. It never logs ``prompt`` or the generated text.
        """
        if self._effective_api_key() is None:
            logger.info("llm_client: no usable GEMINI_API_KEY; returning fallback")
            return self._fallback(language, attempts=0)

        model_id = model or self._model
        delay = self._backoff_base_seconds
        attempts = 0

        for attempt in range(1, self._max_attempts + 1):
            attempts = attempt
            try:
                call = self._resolve_call()
                response = await asyncio.wait_for(
                    call(model=model_id, prompt=prompt, system_instruction=system_instruction),
                    timeout=self._timeout_seconds,
                )
            except Exception as exc:  # noqa: BLE001 — classified below, never re-raised
                transient = _is_transient(exc)
                logger.warning(
                    "llm_client: attempt %d/%d failed (%s, transient=%s, model=%s)",
                    attempt,
                    self._max_attempts,
                    type(exc).__name__,
                    transient,
                    model_id,
                )
                if not transient:
                    break  # e.g. invalid API key — retrying cannot help
                if attempt < self._max_attempts:
                    await self._sleep(delay)
                    delay *= 2
                continue

            result = self._result_from_response(response, attempts=attempts)
            if result is not None:
                return result
            # A response with no text (e.g. fully blocked) is not retryable content.
            logger.warning(
                "llm_client: empty response text on attempt %d (model=%s)", attempt, model_id
            )
            break

        return self._fallback(language, attempts=attempts)
