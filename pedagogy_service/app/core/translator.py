"""Translator service for converting homework prompts and explanations between Khmer and English."""

from __future__ import annotations

import logging
from typing import Any

from dal.llm_client import LlmClient, LlmResult
from dal.schemas.enums import Language, UserMode

logger = logging.getLogger(__name__)


import os
from pathlib import Path
import yaml

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"


class TranslatorService:
    """Translates homework queries and explanations dynamically between Khmer and English."""

    def __init__(
        self,
        llm_client: LlmClient | None = None,
        prompts_dir: Path = PROMPTS_DIR,
    ) -> None:
        self._llm_client = llm_client or LlmClient()
        self._prompts_dir = prompts_dir
        self._spec: dict[str, Any] = self._load_spec()

    def _load_spec(self) -> dict[str, Any]:
        path = self._prompts_dir / "translator.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "system_instruction" in data:
                return data
        # Fallback default spec if file unreadable
        return {
            "system_instruction": "You are an expert educational translator for Cambodian K-12 school homework. Translate the given text into natural {target_name}. Output ONLY translated text.",
            "target_names": {"km": "Khmer script", "en": "English"},
            "mode_instructions": {
                "student": "Ensure translated text encourages the student.",
                "parent": "Provide a clear translation suitable for a parent.",
            },
        }

    async def translate(
        self,
        text: str,
        target_language: Language | str,
        source_language: Language | str | None = None,
        mode: UserMode | str = UserMode.STUDENT,
    ) -> dict[str, Any]:
        """Translate text into target_language dynamically."""
        target_lang = Language(target_language) if isinstance(target_language, str) else target_language
        user_mode = UserMode(mode) if isinstance(mode, str) else mode

        if not text or not text.strip():
            return {
                "translated_text": "",
                "target_language": target_lang.value,
                "from_fallback": False,
            }

        target_name = self._spec.get("target_names", {}).get(target_lang.value, "target language")
        mode_instruction = self._spec.get("mode_instructions", {}).get(user_mode.value, "")

        system_instruction = self._spec["system_instruction"].format(
            target_name=target_name,
            mode_instruction=mode_instruction,
        )

        result: LlmResult = await self._llm_client.generate(
            text,
            language=target_lang,
            system_instruction=system_instruction,
        )

        return {
            "translated_text": result.text.strip(),
            "target_language": target_lang.value,
            "from_fallback": result.from_fallback,
        }
