import sys
from pathlib import Path

import pytest

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from app.core.textbook_chunker import chunk_document
from app.core.retriever import VectorRetriever
from app.ingest.seed_textbooks import DEFAULT_CHUNKS

pytestmark = pytest.mark.anyio


async def test_retriever_adds_and_searches():
    retriever = VectorRetriever()
    await retriever.add_chunks(DEFAULT_CHUNKS)
    assert len(retriever.chunks) == len(DEFAULT_CHUNKS)

    # Search for fractions
    results = await retriever.retrieve(query="របៀបបូកប្រភាគ", grade=4, subject="math", top_k=2)
    assert len(results) > 0
    assert results[0].grade == 4
    assert results[0].subject == "math"
    assert "ប្រភាគ" in results[0].title_khmer or "Fractions" in results[0].title_eng


async def test_chunk_document():
    doc = chunk_document(
        doc_id="tb-test",
        grade=5,
        subject="science",
        topic="plants",
        title_khmer="រស្មីសំយោគ",
        title_eng="Photosynthesis",
        content_khmer="កថាខណ្ឌទី១\n\nកថាខណ្ឌទី២",
        content_eng="Paragraph 1\n\nParagraph 2",
    )
    assert len(doc) == 2
    assert doc[0].id == "tb-test-chunk-1"
    assert doc[1].id == "tb-test-chunk-2"
