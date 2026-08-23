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

def build_socratic_fallback(prompt: str, language: Language | str, grade: int = 4) -> str:
    """Generate dynamic single-step Socratic math explanation fallback when LLM is offline or quota-limited."""
    import re

    def to_ascii_digits(text: str) -> str:
        km_digits = "០១២៣៤៥៦៧៨៩"
        for i, d in enumerate(km_digits):
            text = text.replace(d, str(i))
        return text

    lang_str = str(language.value if hasattr(language, "value") else language).lower()
    is_km = lang_str == "km" or lang_str == "khmer"

    clean_prompt = to_ascii_digits(prompt.strip())
    match_op = re.search(r"(\d+)\s*([\+\-\*\/×÷])\s*(\d+)", clean_prompt)

    if match_op:
        n1_str, op, n2_str = match_op.groups()
        n1 = int(n1_str)
        n2 = int(n2_str)

        if op in ("+", "plus"):
            if n1 < 10 and n2 < 10:
                if is_km:
                    return (
                        f"ដើម្បីបូក {n1} + {n2} ៖ ស្រមៃថាអ្នកមានផ្លែប៉ោម {n1} ផ្លែ នៅក្នុងចានទីមួយ និង {n2} ផ្លែ នៅក្នុងចានទីពីរ! 🍎\n\n"
                        f"ជំហានទី ១៖ តោះរាប់ផ្លែប៉ោមទាំង {n2} ផ្លែបន្ថែមពីលើ {n1} ផ្លែ។ តើអ្នកទទួលបានចំនួនសរុបប៉ុន្មាន? 🐰"
                    )
                else:
                    return (
                        f"To add {n1} + {n2}: Imagine having {n1} apples in one bowl and {n2} apples in another bowl! 🍎\n\n"
                        f"Step 1: Let's count {n2} apples starting after {n1}. What total do you get? 🐰"
                    )
            else:
                ones1, ones2 = n1 % 10, n2 % 10
                tens1, tens2 = n1 - ones1, n2 - ones2
                if is_km:
                    return (
                        f"ដើម្បីបូក {n1} + {n2} ៖ យើងអាចបំបែកតាមខ្ទង់រាយ និងខ្ទង់ដប់ (ឧទាហរណ៍ {n1} = {tens1} + {ones1} និង {n2} = {tens2} + {ones2})! 🍎\n\n"
                        f"ជំហានទី ១៖ តោះបូកខ្ទង់រាយមុនគេ៖ {ones1} + {ones2} = ? តើអ្នកទទួលបានប៉ុន្មាន? 🐰"
                    )
                else:
                    return (
                        f"To add {n1} + {n2}: We can break by place value ({n1} = {tens1} + {ones1} and {n2} = {tens2} + {ones2})! 🍎\n\n"
                        f"Step 1: First, let's add the ones digits: {ones1} + {ones2} = ? What do you get? 🐰"
                    )

        elif op in ("*", "×", "x"):
            if n1 < 10 and n2 < 10:
                if is_km:
                    return (
                        f"ដើម្បីគណនា {n1} × {n2} ៖ ស្រមៃថាអ្នកមានប្រអប់ចំនួន {n1} ហើយក្នុងមួយប្រអប់មានផ្លែប៉ោម {n2} ផ្លែ! 🍎\n\n"
                        f"ជំហានទី ១៖ តោះបូក {n2} ចំនួន {n1} ដង។ តើអ្នកទទួលបានចំនួនសរុបប៉ុន្មាន? 🐰"
                    )
                else:
                    return (
                        f"To calculate {n1} × {n2}: Imagine having {n1} boxes with {n2} apples in each box! 🍎\n\n"
                        f"Step 1: What is {n1} groups of {n2}? 🐰"
                    )
            else:
                tens2 = (n2 // 10) * 10
                ones2 = n2 % 10
                if is_km:
                    return (
                        f"ដើម្បីគណនា {n1} × {n2} ៖ យើងអាចបំបែកលេខ {n2} ជា ({tens2} + {ones2})! 🍎\n"
                        f"ដូច្នេះ {n1} × {n2} = ({n1} × {tens2}) + ({n1} × {ones2})។\n\n"
                        f"ជំហានទី ១៖ តោះគណនាផ្នែកតូចមុនគេ៖ {n1} × {ones2} = ? តើអ្នកទទួលបានប៉ុន្មាន? 🐰"
                    )
                else:
                    return (
                        f"To calculate {n1} × {n2}: We can split {n2} into ({tens2} + {ones2})! 🍎\n"
                        f"So {n1} × {n2} = ({n1} × {tens2}) + ({n1} × {ones2}).\n\n"
                        f"Step 1: Let's compute the smaller part first: What is {n1} × {ones2}? 🐰"
                    )

        elif op in ("-", "minus"):
            if is_km:
                return (
                    f"ដើម្បីដក {n1} - {n2} ៖ ស្រមៃថាអ្នកមានផ្លែប៉ោម {n1} ផ្លែ ហើយអ្នកចែកទៅមិត្តភក្តិ {n2} ផ្លែ! 🍎\n\n"
                    f"ជំហានទី ១៖ ប្រសិនបើដក {n2} ផ្លែចេញពី {n1} ផ្លែ តើអ្នកនៅសល់ផ្លែប៉ោមប៉ុន្មាន? 🐰"
                )
            else:
                return (
                    f"To subtract {n1} - {n2}: Imagine you have {n1} apples and give away {n2} apples! 🍎\n\n"
                    f"Step 1: How many apples do you have left? 🐰"
                )

        elif op in ("/", "÷"):
            if is_km:
                return (
                    f"ដើម្បីចែក {n1} ÷ {n2} ៖ ស្រមៃថាអ្នកមានផ្លែប៉ោម {n1} ផ្លែ ចង់ចែកស្មើៗគ្នាទៅមនុស្ស {n2} នាក់! 🍎\n\n"
                    f"ជំហានទី ១៖ តើម្នាក់ៗទទួលបានផ្លែប៉ោមប៉ុន្មានផ្លែ? 🐰"
                )
            else:
                return (
                    f"To divide {n1} ÷ {n2}: Imagine sharing {n1} apples equally among {n2} people! 🍎\n\n"
                    f"Step 1: How many apples does each person get? 🐰"
                )

    if is_km:
        return (
            f"{FALLBACK_TEXT[Language.KHMER]}\n\n"
            "ជំហានទី ១៖ តើអ្នកគិតថាតម្រុយ ឬពាក្យគន្លឹះដំបូងគេនៅក្នុងសំណួរនេះជាអ្វីដែរ?"
        )
    return (
        f"{FALLBACK_TEXT[Language.ENGLISH]}\n\n"
        "Step 1: What is the first key clue or number you notice in this question?"
    )


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
    def _fallback(language: Language, attempts: int, prompt: str = "") -> LlmResult:
        fallback_str = build_socratic_fallback(prompt, language) if prompt else FALLBACK_TEXT.get(Language(language), FALLBACK_TEXT[Language.KHMER])
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
    ) -> LlmResult:
        """Generate a completion; on any failure return the bilingual fallback.

        This method never raises. It never logs ``prompt`` or the generated text.
        """
        if self._provider != "ollama" and self._effective_api_key() is None:
            logger.info("llm_client: no usable GEMINI_API_KEY; returning fallback")
            return self._fallback(language, attempts=0, prompt=prompt)

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

        return self._fallback(language, attempts=attempts, prompt=prompt)
