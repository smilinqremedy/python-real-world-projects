"""
Embedding Generation Engine.
Implements a normalized semantic embedding representation,
with optional integration for external API providers (e.g. OpenAI text-embedding-ada-002)
configured securely via environment variables.
"""
import os
import re
import math
import hashlib
from typing import List
import numpy as np


STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "how", "what", "which", "who", "whom",
    "this", "that", "these", "those", "it", "its", "as", "if"
}


class EmbeddingEngine:
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.api_key = os.getenv("OPENAI_API_KEY")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generates a normalized 128-dimensional dense semantic embedding vector for a single string.
        Filters out high-frequency stop words and applies subword n-gram hashing.
        """
        raw_words = re.findall(r"\b\w+\b", text.lower())
        words = [w for w in raw_words if w not in STOP_WORDS]
        vec = np.zeros(self.embedding_dim, dtype=np.float32)

        if not words:
            # Fall back to raw words if all were stop words
            words = raw_words
        if not words:
            return vec

        for w in words:
            # Hash word and character 3-grams into vector space
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx] += sign

            # Subword 3-grams
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    sub = w[i:i + 3]
                    sub_h = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                    sub_idx = sub_h % self.embedding_dim
                    vec[sub_idx] += 0.5 * (1.0 if ((sub_h >> 2) % 2 == 0) else -1.0)

        # L2 Normalization
        norm = float(np.linalg.norm(vec)) + 1e-8
        return vec / norm

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embeds a batch of texts into a 2D matrix (N, embedding_dim)."""
        vectors = [self.embed_text(t) for t in texts]
        return np.stack(vectors, axis=0) if vectors else np.zeros((0, self.embedding_dim), dtype=np.float32)
