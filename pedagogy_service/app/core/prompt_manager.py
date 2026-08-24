"""PromptManager — owns all dynamic prompt loading, caching, and assembly.

This module is the single source of truth for everything prompt-related in
the pedagogy service. Nothing else should touch the YAML files directly.

Responsibilities:
- **Band table**: grade ranges → YAML file mapping (a lookup, not an if-chain).
- **YAML loading & caching**: reads all prompt files once at startup.
- **System instruction assembly**: base template + language instruction +
  mode block + optional misconception coaching note.
- **User prompt assembly**: student message + optional step context string.

What this module does NOT do:
- No LLM calls (that is ExplanationGenerator's job).
- No FastAPI imports.
- No database access.

To add a new grade band (e.g. grade7_9):
  1. Fill in ``explain_grade7_9.yaml`` in ``app/ai/prompts/``.
  2. Add a ``Band`` row to ``BANDS`` below.
  That is the entire change — no code paths to modify.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dal.schemas.enums import Language, UserMode

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"

# ---------------------------------------------------------------------------
# Band table
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Band:
    """One grade band and the YAML file that speaks its reading level."""

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


BANDS: tuple[Band, ...] = (
    Band(name="grade1_3", low=1, high=3, prompt_file="explain_grade1_3.yaml"),
    Band(name="grade4_6", low=4, high=6, prompt_file="explain_grade4_6.yaml"),
    Band(name="grade7_9", low=7, high=9, prompt_file="explain_grade7_9.yaml"),
    Band(name="grade10_12", low=10, high=12, prompt_file="explain_grade10_12.yaml"),
)


def band_for_grade(grade: int, bands: tuple[Band, ...] = BANDS) -> Band:
    """Pick the band containing ``grade``, or the nearest one when unmapped.

    ``min`` over (distance, table order): an in-band grade has distance 0;
    grade 8 lands on grade4_6 (distance 2) instead of raising.
    """
    return min(bands, key=lambda b: b.distance(grade))


# ---------------------------------------------------------------------------
# PromptManager
# ---------------------------------------------------------------------------

class PromptManager:
    """Loads and caches all prompt YAML files once, then exposes assembly helpers.

    Parameters
    ----------
    prompts_dir:
        Directory that contains the band YAML files. Overridable for tests.
    bands:
        The band table. Overridable for tests that want a minimal single-band setup.

    Usage
    -----
    Instantiate once at application startup (e.g. in ``ExplanationGenerator.__init__``).
    All ``build_*`` methods are pure (no I/O after init) and safe to call concurrently.
    """

    def __init__(
        self,
        prompts_dir: Path = PROMPTS_DIR,
        bands: tuple[Band, ...] = BANDS,
    ) -> None:
        self._bands = bands
        self._specs: dict[str, dict[str, Any]] = {}
        for band in bands:
            path = prompts_dir / band.prompt_file
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "system_instruction" not in data:
                raise ValueError(
                    f"Prompt file '{path}' is missing required key 'system_instruction'."
                )
            self._specs[band.name] = data

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def band_for(self, grade: int) -> Band:
        """Return the Band object for the given grade."""
        return band_for_grade(grade, self._bands)

    def spec_for(self, grade: int) -> dict[str, Any]:
        """Return the raw YAML dict for the grade band."""
        return self._specs[self.band_for(grade).name]

    def available_misconception_codes(self, grade: int) -> list[str]:
        """Return the list of misconception codes defined for this band's YAML."""
        return list(self.spec_for(grade).get("misconception_instructions", {}).keys())

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def build_system_instruction(
        self,
        *,
        grade: int,
        language: Language,
        mode: UserMode,
        misconception_code: str | None = None,
    ) -> str:
        """Assemble the full Gemini system instruction for a tutoring turn.

        Layers (in order):
        1. Base template with ``{language_instruction}`` slot filled.
        2. Mode block (student: never reveal answer; parent: reveal + explain).
        3. Misconception coaching note — appended ONLY when a code is given,
           as a private instruction block visible only to the model.

        Parameters
        ----------
        grade:
            Student's grade (1–12). Unmapped grades fall back to nearest band.
        language:
            ``Language.KHMER`` or ``Language.ENGLISH``.
        mode:
            ``UserMode.STUDENT`` or ``UserMode.PARENT``.
        misconception_code:
            One of the stable codes emitted by ``grading_service``
            (e.g. ``place_value_error``, ``operation_confusion``).
            ``None`` → generic Socratic explanation with no misconception targeting.
        """
        spec = self._specs[band_for_grade(grade, self._bands).name]

        language_instruction = spec.get("language_instructions", {}).get(Language(language).value, "")
        mode_block = spec.get("mode_instructions", {}).get(UserMode(mode).value, "")
        system_instruction_tmpl = spec.get("system_instruction", "")

        if "{language_instruction}" in system_instruction_tmpl:
            base = system_instruction_tmpl.format(
                language_instruction=language_instruction
            )
        else:
            base = system_instruction_tmpl

        result = base.rstrip()
        if mode_block:
            result = f"{result}\n{mode_block.rstrip()}"

        if misconception_code:
            note = spec.get("misconception_instructions", {}).get(misconception_code)
            if note:
                result += (
                    f"\n\nSpecific Coaching Note for This Student:\n{note.rstrip()}"
                )

        if mode == UserMode.STUDENT:
            guard = (
                "\n\n[CRITICAL SAFETY GUARD]:\n"
                "Throughout the entire conversation, you must NEVER solve, calculate, or provide the direct answer/solution "
                "for the student's exact problem or original numbers. "
                "Whenever the student asks about a specific math/science question or word problem containing numbers, "
                "or when they ask follow-up questions about it, you must ONLY discuss, explain, and solve a worked example "
                "using different numbers. "
                "Keep the explanations simple, clear, and easy to understand. "
                "Always direct the student to apply the worked example's steps to solve their own problem."
            )
            result += guard

        return result

    @staticmethod
    def build_user_prompt(prompt: str, context: str | None) -> str:
        """Combine the student's message with optional problem/step context.

        Context is the compact string built by the orchestrator's explain node
        (problem title + statement + current step question + optional misconception
        suffix). It rides along as a labelled block so the model can distinguish
        context from the student's own words.
        """
        if context:
            return f"{prompt}\n\nContext: {context}"
        return prompt
