"""Vector retriever index supporting cosine similarity and metadata filtering."""

from __future__ import annotations

import numpy as np
from typing import Any

from app.core.embeddings import EmbeddingGenerator
from app.core.textbook_chunker import TextbookChunk


class VectorRetriever:
    def __init__(self, embedder: EmbeddingGenerator | None = None) -> None:
        self.embedder = embedder or EmbeddingGenerator()
        self.chunks: list[TextbookChunk] = []
        self._vectors: np.ndarray | None = None

    async def add_chunks(self, chunks: list[TextbookChunk]) -> None:
        """Embed and index textbook chunks."""
        for chunk in chunks:
            if not chunk.vector:
                # Combine bilingual text for embedding
                combined = f"{chunk.topic} {chunk.title_khmer} {chunk.title_eng} {chunk.text_khmer} {chunk.text_eng}"
                chunk.vector = await self.embedder.embed(combined)
            self.chunks.append(chunk)

        if self.chunks:
            self._vectors = np.array([c.vector for c in self.chunks], dtype=np.float32)

    async def retrieve(
        self,
        query: str,
        grade: int | None = None,
        subject: str | None = None,
        top_k: int = 3,
    ) -> list[TextbookChunk]:
        """Search top-k most relevant textbook chunks matching query and filters."""
        if not self.chunks or self._vectors is None:
            return []

        q_vec = np.array(await self.embedder.embed(query), dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Filter indices by metadata
        candidates = []
        for idx, chunk in enumerate(self.chunks):
            if grade is not None and chunk.grade != grade:
                continue
            if subject is not None and chunk.subject.lower() != subject.lower():
                continue
            candidates.append(idx)

        if not candidates:
            # Fallback to grade-only or all if strict filter is empty
            candidates = list(range(len(self.chunks)))

        candidate_vectors = self._vectors[candidates]
        # Compute cosine similarity
        similarities = np.dot(candidate_vectors, q_vec)

        # Sort descending
        ranked_order = np.argsort(-similarities)[:top_k]

        results: list[TextbookChunk] = []
        for r_idx in ranked_order:
            orig_idx = candidates[r_idx]
            chunk_copy = self.chunks[orig_idx].model_copy()
            chunk_copy.similarity_score = float(similarities[r_idx])
            results.append(chunk_copy)

        return results
