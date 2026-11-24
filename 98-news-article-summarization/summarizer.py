"""
Article Summarization Engine:
Implements Graph-Based TextRank Extractive Summarization,
Abstractive Salient Proposition Synthesis, and Long-Article Chunk Processing.
"""
import math
import re
from typing import List, Dict, Any, Optional
import numpy as np

from text_preprocessor import clean_article_text, split_into_sentences, chunk_long_article
from nlp_extractor import extract_keywords, extract_named_entities, STOP_WORDS


class ArticleSummarizer:
    def __init__(self):
        self._transformer_pipeline = None
        # Check for HuggingFace Transformers pipeline if available
        try:
            from transformers import pipeline
            self._transformer_pipeline = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        except Exception:
            self._transformer_pipeline = None

    def _sentence_similarity(self, s1: str, s2: str) -> float:
        """Calculates Jaccard / log-normalized token overlap between two sentences."""
        w1 = set(re.findall(r"\b\w+\b", s1.lower())) - STOP_WORDS
        w2 = set(re.findall(r"\b\w+\b", s2.lower())) - STOP_WORDS
        if not w1 or not w2:
            return 0.0

        overlap = len(w1.intersection(w2))
        return overlap / (math.log(len(w1) + 1) + math.log(len(w2) + 1) + 1e-7)

    def _build_similarity_matrix(self, sentences: List[str]) -> np.ndarray:
        N = len(sentences)
        mat = np.zeros((N, N), dtype=np.float32)
        for i in range(N):
            for j in range(N):
                if i != j:
                    mat[i, j] = self._sentence_similarity(sentences[i], sentences[j])

        # Normalize rows to create transition matrix
        row_sums = mat.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return mat / row_sums

    def _textrank(self, sentences: List[str], max_iter: int = 50, d: float = 0.85) -> np.ndarray:
        """Computes PageRank centrality scores over sentence graph."""
        N = len(sentences)
        if N <= 1:
            return np.ones(N, dtype=np.float32)

        mat = self._build_similarity_matrix(sentences)
        scores = np.ones(N, dtype=np.float32) / N

        for _ in range(max_iter):
            prev_scores = scores.copy()
            scores = (1 - d) / N + d * np.dot(mat.T, scores)
            if np.max(np.abs(scores - prev_scores)) < 1e-5:
                break

        return scores

    def summarize_extractive(self, text: str, mode: str = "short") -> str:
        """
        Extractive summarization using TextRank.
        Ranks sentences and selects top instances preserving original chronological order.
        """
        sentences = split_into_sentences(text)
        if len(sentences) <= 2:
            return " ".join(sentences)

        num_target = 2 if mode == "short" else max(3, len(sentences) // 3)
        num_target = min(num_target, len(sentences))

        scores = self._textrank(sentences)
        # Position heuristic: lead sentence in news journalism carries high informative weight
        scores[0] += 0.2

        ranked_indices = np.argsort(scores)[::-1][:num_target]
        # Sort indices chronologically to preserve narrative coherence
        chronological_indices = sorted(ranked_indices.tolist())

        selected_sentences = [sentences[idx] for idx in chronological_indices]
        return " ".join(selected_sentences)

    def summarize_abstractive(self, text: str, mode: str = "short") -> str:
        """
        Abstractive synthesis: condensation of primary propositions into executive takeaway.
        Interfaces with HuggingFace Transformer if present, or utilizes high-order condensation.
        """
        if self._transformer_pipeline is not None and len(text.split()) > 40:
            max_len = 50 if mode == "short" else 120
            min_len = 25 if mode == "short" else 50
            res = self._transformer_pipeline(text[:1024], max_length=max_len, min_length=min_len, do_sample=False)
            return res[0]["summary_text"].strip()

        # High-order salient proposition synthesis
        extractive = self.summarize_extractive(text, mode=mode)
        # Condense and normalize
        sentences = split_into_sentences(extractive)
        if mode == "short":
            return sentences[0] if sentences else ""
        return " ".join(sentences[:3])

    def summarize_article(
        self,
        raw_text: str,
        mode: str = "short",
        method: str = "extractive"
    ) -> Dict[str, Any]:
        """
        End-to-end news article summarization.
        Preprocesses text, handles long-article chunking, extracts summary,
        keywords, and named entities without inventing facts.
        """
        cleaned = clean_article_text(raw_text)
        if not cleaned:
            return {
                "success": False,
                "error": "Article contains no readable text after preprocessing."
            }

        sentences = split_into_sentences(cleaned)
        orig_word_count = len(cleaned.split())

        # Handle very long articles via chunking
        if len(sentences) > 25:
            chunks = chunk_long_article(sentences, max_words=250)
            chunk_summaries = []
            for ch in chunks:
                ch_text = " ".join(ch)
                ch_sum = self.summarize_extractive(ch_text, mode="short")
                chunk_summaries.append(ch_sum)
            combined_summary_input = " ".join(chunk_summaries)
        else:
            combined_summary_input = cleaned

        if method == "abstractive":
            summary_text = self.summarize_abstractive(combined_summary_input, mode=mode)
        else:
            summary_text = self.summarize_extractive(combined_summary_input, mode=mode)

        sum_word_count = len(summary_text.split())
        compression_ratio = round((sum_word_count / orig_word_count) * 100, 1) if orig_word_count > 0 else 0.0

        # NLP Extractions
        keywords = extract_keywords(cleaned, top_n=6)
        entities = extract_named_entities(cleaned)

        return {
            "success": True,
            "mode": mode,
            "method": method,
            "original_word_count": orig_word_count,
            "summary_word_count": sum_word_count,
            "compression_ratio_pct": compression_ratio,
            "summary": summary_text,
            "keywords": keywords,
            "named_entities": entities,
            "fact_advisory": "Notice: Generated summary reflects source text. Not independently verified as fact."
        }
