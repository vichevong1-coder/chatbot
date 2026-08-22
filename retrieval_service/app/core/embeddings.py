"""Embedding generator with Gemini embedding API and deterministic local fallback."""

from __future__ import annotations

import hashlib
import os
import struct
import numpy as np


class EmbeddingGenerator:
    def __init__(self, api_key: str | None = None, dim: int = 256) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        """Compute an embedding vector for given text."""
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * self.dim

        if self.api_key:
            try:
                import httpx
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
                    f"?key={self.api_key}"
                )
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": cleaned}]},
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        values = res.json().get("embedding", {}).get("values", [])
                        if values:
                            return values
            except Exception:
                pass

        # Deterministic pseudo-embedding for testing / offline operation
        return self._deterministic_vector(cleaned)

    def _deterministic_vector(self, text: str) -> list[float]:
        """Generate a deterministic normalized vector based on character n-grams and hashing."""
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % self.dim
            vec[idx] += 1.0 / (1.0 + i * 0.1)

        # Add character bi-grams for Khmer / script sensitivity
        for j in range(len(text) - 1):
            bg = text[j : j + 2]
            h = int(hashlib.sha256(bg.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % self.dim
            vec[idx] += 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
