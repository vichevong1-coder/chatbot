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

        # Intercept math prompts to strictly enforce worked example pedagogy
        from dal.fallback_engine import FallbackTemplateEngine
        import re

        DEFAULT_WORKED_EXAMPLE_TEMPLATES = {
            "quadratic": (
                "The student is asking to solve a quadratic equation: {a:g}x^2 + ({b:g})x + ({c:g}) = 0. "
                "Do NOT solve or output the solution for the student's original equation directly. "
                "Instead, use the similar equation {a_ex:g}x^2 + ({b_ex:g})x + ({c_ex:g}) = 0 as a worked example. "
                "Structure your response as follows: "
                "1. Greet the student warmly as Tunsay 🐰. "
                "2. Explain that you will show them how to solve a similar quadratic equation: {a_ex:g}x^2 + ({b_ex:g})x + ({c_ex:g}) = 0. "
                "3. Show the simple step-by-step solution for this worked example (Step 1: Move the constant; Step 2: Complete the square; Step 3: Solve for x). "
                "4. Show the final roots for this worked example. "
                "5. Invite the student to apply these exact steps to solve their original equation: {a:g}x^2 + ({b:g})x + ({c:g}) = 0."
            ),
            "linear": (
                "The student is asking to solve a linear equation: {a:g}x + ({b:g}) = {c:g}. "
                "Do NOT solve or output the solution for the student's original equation directly. "
                "Instead, use the similar equation {a_ex:g}x + ({b_ex:g}) = {c_ex:g} as a worked example. "
                "Structure your response as follows: "
                "1. Greet the student warmly as Tunsay 🐰. "
                "2. Explain that you will show them how to solve a similar linear equation: {a_ex:g}x + ({b_ex:g}) = {c_ex:g}. "
                "3. Show the simple step-by-step solution for this worked example (Step 1: Isolate the variable term; Step 2: Divide to solve for x). "
                "4. Show the final answer of the worked example. "
                "5. Invite the student to apply these exact steps to solve their original equation: {a:g}x + ({b:g}) = {c:g}."
            ),
            "arithmetic": (
                "The student is asking to calculate: {expr}. "
                "Do NOT calculate or output the answer to the student's original expression directly. "
                "Instead, use the similar expression {expr_ex} as a worked example. "
                "Structure your response as follows: "
                "1. Greet the student warmly as Tunsay 🐰. "
                "2. Explain that you will show them how to solve a similar calculation: {expr_ex}. "
                "3. Show the step-by-step calculation/method for this worked example. "
                "4. Show the final answer of the worked example. "
                "5. Invite the student to calculate their original expression {expr} using the same method."
            ),
            "word_problem": (
                "The student's original query is: \"{prompt}\"\n"
                "Do NOT solve or calculate the student's original problem directly. "
                "Instead, use a similar worked example with different numbers (for example: {suggestions}). "
                "Structure your response as follows: "
                "1. Greet the student warmly as Tunsay 🐰. "
                "2. Present the worked example clearly using the alternate numbers (e.g. if the original problem asks about adding 3 and 4, make the worked example about adding 5 and 6). "
                "3. Show the simple step-by-step solution for this worked example. Keep it very simple, friendly, and easy to understand (do NOT use algebra, variables, or complex math definitions). "
                "4. State the final answer of the worked example clearly. "
                "5. Invite the student to use these exact same steps to solve their original problem: \"{prompt}\"."
            )
        }

        spec = self._pm.spec_for(grade)
        templates = spec.get("worked_example_templates", {})
        
        quad = FallbackTemplateEngine.parse_quadratic(prompt)
        if quad:
            a, b, c = quad
            if a == 1 and b == 6 and c == -3:
                a_ex, b_ex, c_ex = 1.0, 8.0, -5.0
            else:
                a_ex, b_ex, c_ex = 1.0, 6.0, -3.0
            
            tmpl = templates.get("quadratic", DEFAULT_WORKED_EXAMPLE_TEMPLATES["quadratic"])
            prompt = tmpl.format(a=a, b=b, c=c, a_ex=a_ex, b_ex=b_ex, c_ex=c_ex)
        else:
            lin = FallbackTemplateEngine.parse_linear(prompt)
            if lin:
                a, b, c = lin
                if a == 2 and b == 6 and c == 16:
                    a_ex, b_ex, c_ex = 3.0, 4.0, 19.0
                else:
                    a_ex, b_ex, c_ex = 2.0, 6.0, 16.0
                
                tmpl = templates.get("linear", DEFAULT_WORKED_EXAMPLE_TEMPLATES["linear"])
                prompt = tmpl.format(a=a, b=b, c=c, a_ex=a_ex, b_ex=b_ex, c_ex=c_ex)
            else:
                arith = FallbackTemplateEngine.parse_arithmetic(prompt)
                if arith:
                    expr, _ = arith
                    match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", expr)
                    if match:
                        n1_str, op, n2_str = match.groups()
                        n1, n2 = float(n1_str), float(n2_str)
                        n1_ex = n1 - 2 if n1 > 2 else n1 + 3
                        n2_ex = n2 - 1 if n2 > 1 else n2 + 2
                        expr_ex = f"{n1_ex:g} {op} {n2_ex:g}"
                        
                        tmpl = templates.get("arithmetic", DEFAULT_WORKED_EXAMPLE_TEMPLATES["arithmetic"])
                        prompt = tmpl.format(expr=expr, expr_ex=expr_ex)
                else:
                    # General number matching for word problems
                    numbers = re.findall(r"\d+(?:\.\d+)?", prompt)
                    if numbers:
                        alt_nums = []
                        for num_str in numbers:
                            try:
                                val = float(num_str)
                                if val.is_integer():
                                    alt_val = int(val) + 2 if val > 2 else int(val) + 3
                                else:
                                    alt_val = val + 1.5
                                alt_nums.append(f"{alt_val:g}")
                            except ValueError:
                                alt_nums.append(num_str)
                        suggestions = ", ".join(f"change {n} to {a}" for n, a in zip(numbers, alt_nums))
                        
                        tmpl = templates.get("word_problem", DEFAULT_WORKED_EXAMPLE_TEMPLATES["word_problem"])
                        prompt = tmpl.format(prompt=prompt, suggestions=suggestions)

        result: LlmResult = await self._llm_client.generate(
            self._pm.build_user_prompt(prompt, context),
            language=language,
            system_instruction=system_instruction,
            context=context,
        )
        return {
            "text_khmer": result.text if language is Language.KHMER else "",
            "text_eng": result.text if language is Language.ENGLISH else "",
            "from_fallback": result.from_fallback,
            "prompt_tokens": result.prompt_tokens,
            "output_tokens": result.output_tokens,
        }
