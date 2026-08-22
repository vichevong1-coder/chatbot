"""Textbook chunker for MoEYS curriculum content."""

from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class TextbookChunk(BaseModel):
    id: str
    grade: int
    subject: str
    topic: str
    title_khmer: str
    title_eng: str
    text_khmer: str
    text_eng: str
    vector: list[float] | None = None
    similarity_score: float | None = None


def chunk_document(
    doc_id: str,
    grade: int,
    subject: str,
    topic: str,
    title_khmer: str,
    title_eng: str,
    content_khmer: str,
    content_eng: str,
    max_chunk_chars: int = 500,
) -> list[TextbookChunk]:
    """Split textbook document into semantic bilingual chunks."""
    paragraphs_km = [p.strip() for p in re.split(r"\n\s*\n", content_khmer) if p.strip()]
    paragraphs_en = [p.strip() for p in re.split(r"\n\s*\n", content_eng) if p.strip()]

    chunks: list[TextbookChunk] = []
    total = max(len(paragraphs_km), len(paragraphs_en), 1)

    for i in range(total):
        km = paragraphs_km[i] if i < len(paragraphs_km) else (paragraphs_km[-1] if paragraphs_km else "")
        en = paragraphs_en[i] if i < len(paragraphs_en) else (paragraphs_en[-1] if paragraphs_en else "")
        chunks.append(
            TextbookChunk(
                id=f"{doc_id}-chunk-{i+1}",
                grade=grade,
                subject=subject,
                topic=topic,
                title_khmer=title_khmer,
                title_eng=title_eng,
                text_khmer=km,
                text_eng=en,
            )
        )

    return chunks
