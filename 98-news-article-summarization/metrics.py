"""
Summary Quality Evaluation Metrics:
ROUGE-1, ROUGE-2, and ROUGE-L (Longest Common Subsequence).
Includes documentation on automated evaluation metric constraints and limitations.
"""
from typing import Dict, Any, List, Set


def get_ngrams(tokens: List[str], n: int) -> Set[str]:
    """Generates set of n-grams from a list of tokens."""
    return set(" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def longest_common_subsequence(seq1: List[str], seq2: List[str]) -> int:
    """Computes length of the Longest Common Subsequence (LCS)."""
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def compute_rouge(reference: str, summary: str) -> Dict[str, Any]:
    """
    Computes ROUGE-1, ROUGE-2, and ROUGE-L metrics.
    Recall = Overlap / Reference
    Precision = Overlap / Summary
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    """
    ref_tokens = reference.strip().lower().split()
    sum_tokens = summary.strip().lower().split()

    if not ref_tokens or not sum_tokens:
        return {
            "rouge_1": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
            "rouge_2": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
            "rouge_l": {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        }

    # 1. ROUGE-1 (Unigram)
    ref_1 = get_ngrams(ref_tokens, 1)
    sum_1 = get_ngrams(sum_tokens, 1)
    overlap_1 = len(ref_1.intersection(sum_1))

    r1_rec = overlap_1 / len(ref_1) if ref_1 else 0.0
    r1_prec = overlap_1 / len(sum_1) if sum_1 else 0.0
    r1_f1 = (2 * r1_rec * r1_prec) / (r1_rec + r1_prec) if (r1_rec + r1_prec) > 0 else 0.0

    # 2. ROUGE-2 (Bigram)
    ref_2 = get_ngrams(ref_tokens, 2)
    sum_2 = get_ngrams(sum_tokens, 2)
    overlap_2 = len(ref_2.intersection(sum_2))

    r2_rec = overlap_2 / len(ref_2) if ref_2 else 0.0
    r2_prec = overlap_2 / len(sum_2) if sum_2 else 0.0
    r2_f1 = (2 * r2_rec * r2_prec) / (r2_rec + r2_prec) if (r2_rec + r2_prec) > 0 else 0.0

    # 3. ROUGE-L (LCS)
    lcs_len = longest_common_subsequence(ref_tokens, sum_tokens)
    rl_rec = lcs_len / len(ref_tokens) if ref_tokens else 0.0
    rl_prec = lcs_len / len(sum_tokens) if sum_tokens else 0.0
    rl_f1 = (2 * rl_rec * rl_prec) / (rl_rec + rl_prec) if (rl_rec + rl_prec) > 0 else 0.0

    return {
        "rouge_1": {"precision": round(r1_prec, 4), "recall": round(r1_rec, 4), "f1": round(r1_f1, 4)},
        "rouge_2": {"precision": round(r2_prec, 4), "recall": round(r2_rec, 4), "f1": round(r2_f1, 4)},
        "rouge_l": {"precision": round(rl_prec, 4), "recall": round(rl_rec, 4), "f1": round(rl_f1, 4)},
        "metric_limitations_note": (
            "ROUGE evaluates statistical n-gram overlap between candidate and reference texts. "
            "It does NOT verify factual accuracy, semantic coherence, or grammatical flow, "
            "and may penalize valid abstractive paraphrasing that uses synonyms."
        )
    }
