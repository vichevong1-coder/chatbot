"""Grade-banded explanation generation — pure LLM orchestration.

This module now owns exactly ONE thing: calling the LLM and mapping
the result onto the API response shape.

All prompt concerns (band resolution, YAML loading, system instruction
assembly) live in :mod:`app.core.prompt_manager`.

``ExplanationGenerator`` accepts an injectable ``PromptManager`` so tests
can swap in a minimal single-band setup without touching the file system,
and an injectable ``LlmClient`` so tests can swap in a fake ``call``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dal.llm_client import LlmClient, LlmResult
from dal.schemas.enums import Language, UserMode

from app.core.prompt_manager import BANDS, PROMPTS_DIR, Band, PromptManager

# Re-export for callers that previously imported these from here directly
# (keeps backward compatibility with existing tests and conftest.py).
__all__ = ["Band", "BANDS", "PROMPTS_DIR", "band_for_grade", "ExplanationGenerator"]


def band_for_grade(grade: int) -> Band:
    """Thin re-export so existing tests that import from here keep working."""
    from app.core.prompt_manager import band_for_grade as _bfg
    return _bfg(grade)


class ExplanationGenerator:
    """Assembles prompts via PromptManager and calls the LLM.

    Parameters
    ----------
    llm_client:
        Injectable :class:`dal.llm_client.LlmClient`. Tests pass one built with a
        fake ``call``; production omits it and gets the real Gemini-backed client.
    prompt_manager:
        Injectable :class:`~app.core.prompt_manager.PromptManager`. Tests can pass
        a manager built against a minimal YAML fixture; production omits it and
        gets the real one built from ``app/ai/prompts/``.
    prompts_dir:
        Kept for backward compatibility — ignored when ``prompt_manager`` is given.
    """

    def __init__(
        self,
        *,
        llm_client: LlmClient | None = None,
        prompt_manager: PromptManager | None = None,
        prompts_dir: Path = PROMPTS_DIR,
    ) -> None:
        self._llm_client = llm_client or LlmClient()
        self._pm = prompt_manager or PromptManager(prompts_dir=prompts_dir)

    # ------------------------------------------------------------------
    # Thin delegation wrappers (kept for tests that call these directly)
    # ------------------------------------------------------------------

    def build_system_instruction(
        self,
        *,
        grade: int,
        language: Language,
        mode: UserMode,
        misconception_code: str | None = None,
    ) -> str:
        """Delegate to PromptManager.build_system_instruction."""
        return self._pm.build_system_instruction(
            grade=grade,
            language=language,
            mode=mode,
            misconception_code=misconception_code,
        )

    @staticmethod
    def build_prompt(prompt: str, context: str | None) -> str:
        """Thin wrapper kept for backward compatibility with existing tests."""
        return PromptManager.build_user_prompt(prompt, context)

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------

    async def explain(
        self,
        *,
        prompt: str,
        grade: int,
        language: Language,
        mode: UserMode,
        context: str | None = None,
        misconception_code: str | None = None,
    ) -> dict[str, Any]:
        """Generate an explanation; the result shape follows contracts.md §3/§4.

        Never raises for LLM trouble — LlmClient already degrades to the bilingual
        Tunsay-voiced fallback with ``from_fallback=True``.
        """
        language = Language(language)
        system_instruction = self._pm.build_system_instruction(
            grade=grade,
            language=language,
            mode=UserMode(mode),
            misconception_code=misconception_code,
        )
        result: LlmResult = await self._llm_client.generate(
            self._pm.build_user_prompt(prompt, context),
            language=language,
            system_instruction=system_instruction,
        )
        return {
            "text_khmer": result.text if language is Language.KHMER else "",
            "text_eng": result.text if language is Language.ENGLISH else "",
            "from_fallback": result.from_fallback,
            "prompt_tokens": result.prompt_tokens,
            "output_tokens": result.output_tokens,
        }
