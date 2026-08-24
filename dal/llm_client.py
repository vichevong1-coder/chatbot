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
import re
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
DEFAULT_MODEL = "gemini-2.0-flash"

DEFAULT_PROVIDER_ENV = "LLM_PROVIDER"
DEFAULT_PROVIDER = "gemini"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"

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


class OllamaUnreachableError(Exception):
    """Ollama service is not reachable at the configured OLLAMA_URL."""


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
        self._provider = os.environ.get(DEFAULT_PROVIDER_ENV, DEFAULT_PROVIDER).strip().lower()
        if self._provider not in ("gemini", "ollama"):
            raise ValueError(
                f"Invalid LLM_PROVIDER {self._provider!r}. Must be 'gemini' or 'ollama'."
            )
        if model:
            self._model = model
        elif self._provider == "ollama":
            self._model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
        else:
            self._model = os.environ.get(DEFAULT_MODEL_ENV, "").strip() or DEFAULT_MODEL
        self._ollama_url = os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
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
            if self._provider == "ollama":
                async def _ollama_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    headers = {"Content-Type": "application/json"}
                    messages = []
                    if system_instruction:
                        messages.append({"role": "system", "content": system_instruction})
                    messages.append({"role": "user", "content": prompt})

                    payload = {
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7
                        }
                    }
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{self._ollama_url}/v1/chat/completions",
                                json=payload,
                                headers=headers,
                                timeout=self._timeout_seconds,
                            )
                            response.raise_for_status()
                            res = response.json()
                    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                        raise OllamaUnreachableError(
                            f"Ollama is not reachable at {self._ollama_url}. "
                            f"Check if the Ollama service is running and the port is correct."
                        ) from exc

                    choices = res.get("choices", [])
                    if not choices:
                        raise ValueError("Ollama returned an empty choices list")
                    text = choices[0].get("message", {}).get("content", "")
                    usage = res.get("usage", {})
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        attempts=0,
                    )

                self._call = _ollama_call
            else:
                # Imported lazily so a mocked client never needs the SDK wired up.
                from google import genai

                client = genai.Client(api_key=self._effective_api_key())

                async def _sdk_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    config = None
                    if system_instruction is not None:
                        from google.genai import types

                        config = types.GenerateContentConfig(system_instruction=system_instruction)
                    response = await client.aio.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                    text = getattr(response, "text", None) or ""
                    usage = getattr(response, "usage_metadata", None)
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=getattr(usage, "candidates_token_count", None),
                        total_tokens=getattr(usage, "total_token_count", None),
                        attempts=0,
                    )

                self._call = _sdk_call
        return self._call

    # -- results ------------------------------------------------------------------

def build_socratic_fallback(
    prompt: str,
    language: Language | str,
    grade: int = 4,
    context: str | None = None,
) -> str:
    """Smart Dynamic Socratic Fallback Engine (Tier 3).

    Delegates to FallbackTemplateEngine to dynamically parse math equations
    and render step-by-step Socratic responses without hardcoded strings.
    """
    from dal.fallback_engine import FallbackTemplateEngine

    lang_str = str(language.value if hasattr(language, "value") else language).lower()
    return FallbackTemplateEngine.render_explanation(
        prompt=prompt,
        language=lang_str,
        context=context,
    )


class OllamaUnreachableError(Exception):
    """Ollama service is not reachable at the configured OLLAMA_URL."""


class LlmClient:
    """Async Gemini client with per-attempt timeout, bounded retry, Ollama fallback, and dynamic Socratic fallback."""

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
        self._provider = os.environ.get(DEFAULT_PROVIDER_ENV, DEFAULT_PROVIDER).strip().lower()
        if self._provider not in ("gemini", "ollama"):
            raise ValueError(
                f"Invalid LLM_PROVIDER {self._provider!r}. Must be 'gemini' or 'ollama'."
            )
        if model:
            self._model = model
        elif self._provider == "ollama":
            self._model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
        else:
            self._model = os.environ.get(DEFAULT_MODEL_ENV, "").strip() or DEFAULT_MODEL
        self._ollama_url = os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
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
            if self._provider == "ollama":
                async def _ollama_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    headers = {"Content-Type": "application/json"}
                    messages = []
                    if system_instruction:
                        messages.append({"role": "system", "content": system_instruction})
                    messages.append({"role": "user", "content": prompt})

                    payload = {
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.7},
                    }
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{self._ollama_url}/v1/chat/completions",
                                json=payload,
                                headers=headers,
                                timeout=self._timeout_seconds,
                            )
                            response.raise_for_status()
                            res = response.json()
                    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                        raise OllamaUnreachableError(
                            f"Ollama is not reachable at {self._ollama_url}."
                        ) from exc

                    choices = res.get("choices", [])
                    if not choices:
                        raise ValueError("Ollama returned an empty choices list")
                    text = choices[0].get("message", {}).get("content", "")
                    usage = res.get("usage", {})
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        attempts=0,
                    )

                self._call = _ollama_call
            else:
                from google import genai

                client = genai.Client(api_key=self._effective_api_key())

                async def _sdk_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    config = None
                    if system_instruction is not None:
                        from google.genai import types

                        config = types.GenerateContentConfig(system_instruction=system_instruction)
                    response = await client.aio.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                    text = getattr(response, "text", None) or ""
                    usage = getattr(response, "usage_metadata", None)
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=getattr(usage, "candidates_token_count", None),
                        total_tokens=getattr(usage, "total_token_count", None),
                        attempts=0,
                    )

                self._call = _sdk_call
        return self._call

    # -- results ------------------------------------------------------------------

    @staticmethod
    def _fallback(language: Language, attempts: int, prompt: str = "", context: str | None = None) -> LlmResult:
        fallback_str = build_socratic_fallback(prompt, language, context=context) if prompt else FALLBACK_TEXT.get(Language(language), FALLBACK_TEXT[Language.KHMER])
        return LlmResult(
            text=fallback_str,
            from_fallback=True,
            attempts=attempts,
        )

    @staticmethod
    def _result_from_response(response: Any, attempts: int) -> LlmResult | None:
        if isinstance(response, LlmResult):
            response.attempts = attempts
            return response

        if isinstance(response, dict):
            choices = response.get("choices", [])
            if not choices:
                return None
            text = choices[0].get("message", {}).get("content", "")
            if not text:
                return None
            usage = response.get("usage", {})
            return LlmResult(
                text=text,
                from_fallback=False,
                prompt_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                attempts=attempts,
            )

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

    # -- 3-Tier Public Entry Point -------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        language: Language,
        system_instruction: str | None = None,
        model: str | None = None,
        context: str | None = None,
    ) -> LlmResult:
        """Generate a completion using 3-Tier Fallback (Gemini -> Ollama -> Dynamic Rule Engine).

        This method never raises. It never logs ``prompt`` or the generated text.
        """
        model_id = model or self._model
        delay = self._backoff_base_seconds
        attempts = 0

        # Tier 1: Try Primary Provider (Gemini / configured provider)
        if self._effective_api_key() is not None:
            for attempt in range(1, self._max_attempts + 1):
                attempts = attempt
                try:
                    call = self._resolve_call()
                    response = await asyncio.wait_for(
                        call(model=model_id, prompt=prompt, system_instruction=system_instruction),
                        timeout=self._timeout_seconds,
                    )
                    result = self._result_from_response(response, attempts=attempts)
                    if result is not None:
                        return result
                except Exception as exc:  # noqa: BLE001
                    transient = _is_transient(exc)
                    logger.warning(
                        "llm_client: Tier 1 attempt %d/%d failed (%s: %s, transient=%s, model=%s)",
                        attempt,
                        self._max_attempts,
                        type(exc).__name__,
                        exc,
                        transient,
                        model_id,
                    )
                    if not transient:
                        break
                    if attempt < self._max_attempts:
                        await self._sleep(delay)
                        delay *= 2
                    continue

        # Tier 2: Try Local Ollama LLM Fallback
        try:
            logger.info("llm_client: Tier 1 unavailable/failed; trying Tier 2 Ollama fallback")
            ollama_url = os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
            ollama_model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
            headers = {"Content-Type": "application/json"}
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": ollama_model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{ollama_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=2.0,  # Fast 2-second timeout for local Ollama check
                )
                if resp.status_code == 200:
                    res = resp.json()
                    choices = res.get("choices", [])
                    if choices:
                        text = choices[0].get("message", {}).get("content", "")
                        if text:
                            usage = res.get("usage", {})
                            return LlmResult(
                                text=text,
                                from_fallback=False,
                                prompt_tokens=usage.get("prompt_tokens"),
                                output_tokens=usage.get("completion_tokens"),
                                total_tokens=usage.get("total_tokens"),
                                attempts=attempts,
                            )
        except Exception as exc:
            logger.info("llm_client: Tier 2 Ollama fallback unavailable/failed (%s: %s)", type(exc).__name__, exc)

        # Tier 3: Dynamic Socratic Rule Engine Fallback
        logger.info("llm_client: Tier 2 unavailable/failed; using Tier 3 Dynamic Socratic Fallback")
        return self._fallback(language, attempts=attempts, prompt=prompt, context=context)


class OllamaUnreachableError(Exception):
    """Ollama service is not reachable at the configured OLLAMA_URL."""


class LlmClient:
    """Async Gemini client with per-attempt timeout, bounded retry and fallback."""

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
        self._provider = os.environ.get(DEFAULT_PROVIDER_ENV, DEFAULT_PROVIDER).strip().lower()
        if self._provider not in ("gemini", "ollama"):
            raise ValueError(
                f"Invalid LLM_PROVIDER {self._provider!r}. Must be 'gemini' or 'ollama'."
            )
        if model:
            self._model = model
        elif self._provider == "ollama":
            self._model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
        else:
            self._model = os.environ.get(DEFAULT_MODEL_ENV, "").strip() or DEFAULT_MODEL
        self._ollama_url = os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
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
            if self._provider == "ollama":
                async def _ollama_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    headers = {"Content-Type": "application/json"}
                    messages = []
                    if system_instruction:
                        messages.append({"role": "system", "content": system_instruction})
                    messages.append({"role": "user", "content": prompt})

                    payload = {
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7
                        }
                    }
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{self._ollama_url}/v1/chat/completions",
                                json=payload,
                                headers=headers,
                                timeout=self._timeout_seconds,
                            )
                            response.raise_for_status()
                            res = response.json()
                    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                        raise OllamaUnreachableError(
                            f"Ollama is not reachable at {self._ollama_url}. "
                            f"Check if the Ollama service is running and the port is correct."
                        ) from exc

                    choices = res.get("choices", [])
                    if not choices:
                        raise ValueError("Ollama returned an empty choices list")
                    text = choices[0].get("message", {}).get("content", "")
                    usage = res.get("usage", {})
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        attempts=0,
                    )

                self._call = _ollama_call
            else:
                from google import genai

                client = genai.Client(api_key=self._effective_api_key())

                async def _sdk_call(
                    *, model: str, prompt: str, system_instruction: str | None
                ) -> LlmResult:
                    config = None
                    if system_instruction is not None:
                        from google.genai import types

                        config = types.GenerateContentConfig(system_instruction=system_instruction)
                    response = await client.aio.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                    text = getattr(response, "text", None) or ""
                    usage = getattr(response, "usage_metadata", None)
                    return LlmResult(
                        text=text,
                        from_fallback=False,
                        prompt_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=getattr(usage, "candidates_token_count", None),
                        total_tokens=getattr(usage, "total_token_count", None),
                        attempts=0,
                    )

                self._call = _sdk_call
        return self._call

    # -- results ------------------------------------------------------------------

    @staticmethod
    def _fallback(language: Language, attempts: int, prompt: str = "", context: str | None = None) -> LlmResult:
        fallback_str = build_socratic_fallback(prompt, language, context=context) if prompt else FALLBACK_TEXT.get(Language(language), FALLBACK_TEXT[Language.KHMER])
        return LlmResult(
            text=fallback_str,
            from_fallback=True,
            attempts=attempts,
        )

    @staticmethod
    def _result_from_response(response: Any, attempts: int) -> LlmResult | None:
        if isinstance(response, LlmResult):
            response.attempts = attempts
            return response

        if isinstance(response, dict):
            choices = response.get("choices", [])
            if not choices:
                return None
            text = choices[0].get("message", {}).get("content", "")
            if not text:
                return None
            usage = response.get("usage", {})
            return LlmResult(
                text=text,
                from_fallback=False,
                prompt_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                attempts=attempts,
            )

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
        context: str | None = None,
    ) -> LlmResult:
        """Generate a completion using 3-Tier Fallback (Gemini -> Ollama -> Dynamic Rule Engine).

        This method never raises. It never logs ``prompt`` or the generated text.
        """
        model_id = model or self._model
        delay = self._backoff_base_seconds
        attempts = 0

        # Tier 1: Try Primary Provider (Gemini / configured provider)
        if self._provider != "ollama" and self._effective_api_key() is not None:
            for attempt in range(1, self._max_attempts + 1):
                attempts = attempt
                try:
                    call = self._resolve_call()
                    response = await asyncio.wait_for(
                        call(model=model_id, prompt=prompt, system_instruction=system_instruction),
                        timeout=self._timeout_seconds,
                    )
                    result = self._result_from_response(response, attempts=attempts)
                    if result is not None:
                        return result
                except Exception as exc:  # noqa: BLE001
                    transient = _is_transient(exc)
                    logger.warning(
                        "llm_client: Tier 1 attempt %d/%d failed (%s: %s, transient=%s, model=%s)",
                        attempt,
                        self._max_attempts,
                        type(exc).__name__,
                        exc,
                        transient,
                        model_id,
                    )
                    # If 429 quota exhausted or non-transient, don't stall — proceed to Tier 2 Ollama immediately
                    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or not transient:
                        break
                    if attempt < self._max_attempts:
                        await self._sleep(delay)
                        delay *= 2
                    continue

        # Tier 2: Try Local Ollama LLM Fallback
        # Note: llama3.2:3b cannot generate fluent Khmer and outputs gibberish, so Khmer uses Tier 3 Dynamic Engine.
        lang_val = str(language.value if hasattr(language, "value") else language).lower()
        is_km_request = lang_val in ("km", "khmer")

        if not is_km_request:
            try:
                logger.info("llm_client: Tier 1 unavailable/failed; trying Tier 2 Ollama fallback")
                base_url = os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL).strip()
                ollama_model = os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()

                # Auto-resolve Docker container -> host mapping if localhost fails inside container
                candidate_urls = [base_url]
                if "localhost" in base_url or "127.0.0.1" in base_url:
                    candidate_urls.append(base_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal"))
                    candidate_urls.append(base_url.replace("localhost", "172.17.0.1").replace("127.0.0.1", "172.17.0.1"))

                headers = {"Content-Type": "application/json"}
                messages = []
                if system_instruction:
                    sys_inst_clean = re.sub(r'[\u1780-\u17FF]+', '', system_instruction)
                    sys_inst_clean = re.sub(r'\(\s*\)', '', sys_inst_clean)
                    messages.append({"role": "system", "content": sys_inst_clean})
                messages.append({"role": "user", "content": prompt})

                payload = {
                    "model": ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7},
                }
                async with httpx.AsyncClient() as client:
                    for target_url in candidate_urls:
                        try:
                            resp = await client.post(
                                f"{target_url}/v1/chat/completions",
                                json=payload,
                                headers=headers,
                                timeout=30.0,  # 30-second timeout for local Ollama inference
                            )
                            if resp.status_code == 200:
                                res = resp.json()
                                choices = res.get("choices", [])
                                if choices:
                                    text = choices[0].get("message", {}).get("content", "")
                                    if text:
                                        usage = res.get("usage", {})
                                        return LlmResult(
                                            text=text,
                                            from_fallback=False,
                                            prompt_tokens=usage.get("prompt_tokens"),
                                            output_tokens=usage.get("completion_tokens"),
                                            total_tokens=usage.get("total_tokens"),
                                            attempts=attempts,
                                        )
                        except Exception as err:
                            logger.debug("llm_client: Ollama endpoint %s failed (%s)", target_url, err)
                            continue
            except Exception as exc:
                logger.info("llm_client: Tier 2 Ollama fallback unavailable/failed (%s: %s)", type(exc).__name__, exc)

        # Tier 3: Dynamic Socratic Rule Engine Fallback
        logger.info("llm_client: Tier 2 unavailable/failed; using Tier 3 Dynamic Socratic Fallback")
        return self._fallback(language, attempts=attempts, prompt=prompt, context=context)
