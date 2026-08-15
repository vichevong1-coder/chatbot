"""Grade-banded explanation generation — pure orchestration around dal's LlmClient.

This module owns three things and nothing else (no FastAPI imports here):

- the **band table**: grade ranges → prompt YAML, a lookup rather than an ``if``
  chain, so widening grade support is a table edit (.claude/plan.md P1.8);
- **prompt assembly**: band template + language instruction + mode block, all read
  from ``app/ai/prompts/*.yaml`` — the system prompt ported out of
  ``frontend_tunsay/server.ts`` lives in those files, never in code;
- the **LlmClient call** and mapping of its ``LlmResult`` onto the response shape
  (single-language rule, .claude/contracts.md §3: the requested language is filled,
  the other side is ``""``).

Grade *validation* belongs to callers (dal's grade schema); this module accepts any
structurally valid grade 1–12 and maps an unmapped grade (e.g. 8, once config
widens) to the NEAREST implemented band instead of erroring.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dal.llm_client import LlmClient, LlmResult
from dal.schemas.enums import Language, UserMode

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"


@dataclass(frozen=True)
class Band:
    """One grade band and the prompt file that speaks its reading level."""

    name: str
    low: int
    high: int
    prompt_file: str

    def distance(self, grade: int) -> int:
        """0 when ``grade`` is inside the band, else distance to the nearer edge."""
        if grade < self.low:
            return self.low - grade
        if grade > self.high:
            return grade - self.high
        return 0


# The band table (a lookup, not an if-chain). Only *implemented* bands are listed:
# explain_grade7_9.yaml and explain_grade10_12.yaml exist as reserved 0-byte stubs
# (future scope — .claude/claude.md §4); add their rows here when they are filled.
# An unmapped-but-valid grade falls back to the nearest listed band.
BANDS: tuple[Band, ...] = (
    Band(name="grade1_3", low=1, high=3, prompt_file="explain_grade1_3.yaml"),
    Band(name="grade4_6", low=4, high=6, prompt_file="explain_grade4_6.yaml"),
)


def band_for_grade(grade: int, bands: tuple[Band, ...] = BANDS) -> Band:
    """Pick the band containing ``grade``, or the nearest one when unmapped.

    ``min`` over (distance, table order) — a grade inside a band has distance 0,
    and grade 8 lands on grade4_6 (distance 2) rather than raising.
    """
    return min(bands, key=lambda band: band.distance(grade))


class ExplanationGenerator:
    """Loads and caches the prompt YAMLs once, then assembles + generates.

    Parameters
    ----------
    llm_client:
        Injectable :class:`dal.llm_client.LlmClient`. Tests pass one built with a
        fake ``call``; production omits it and gets the real Gemini-backed client.
    prompts_dir:
        Where the band YAMLs live. Overridable for tests.
    """

    def __init__(
        self,
        *,
        llm_client: LlmClient | None = None,
        prompts_dir: Path = PROMPTS_DIR,
    ) -> None:
        self._llm_client = llm_client or LlmClient()
        self._prompts: dict[str, dict[str, Any]] = {}
        for band in BANDS:
            path = prompts_dir / band.prompt_file
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "system_instruction" not in data:
                raise ValueError(f"prompt file {path} is missing 'system_instruction'")
            self._prompts[band.name] = data

    # -- prompt assembly (pure) ---------------------------------------------------

    def build_system_instruction(
        self, *, grade: int, language: Language, mode: UserMode
    ) -> str:
        """Band template + language instruction + mode block, all from YAML."""
        band = band_for_grade(grade)
        spec = self._prompts[band.name]
        language_instruction = spec["language_instructions"][str(Language(language))]
        mode_block = spec["mode_instructions"][str(UserMode(mode))]
        assembled = spec["system_instruction"].format(
            language_instruction=language_instruction
        )
        return f"{assembled.rstrip()}\n{mode_block.rstrip()}"

    @staticmethod
    def build_prompt(prompt: str, context: str | None) -> str:
        """The user-facing part of the request; context rides along when present."""
        if context:
            return f"{prompt}\n\nContext: {context}"
        return prompt

    # -- generation ---------------------------------------------------------------

    async def explain(
        self,
        *,
        prompt: str,
        grade: int,
        language: Language,
        mode: UserMode,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Generate an explanation; the result shape follows contracts.md §3/§4.

        Never raises for LLM trouble — LlmClient already degrades to the bilingual
        Tunsay-voiced fallback with ``from_fallback=True``.
        """
        language = Language(language)
        system_instruction = self.build_system_instruction(
            grade=grade, language=language, mode=UserMode(mode)
        )
        result: LlmResult = await self._llm_client.generate(
            self.build_prompt(prompt, context),
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
