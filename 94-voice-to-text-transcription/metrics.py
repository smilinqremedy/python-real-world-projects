"""
Transcription Accuracy Evaluation Metrics:
Word Error Rate (WER) and Character Error Rate (CER) based on Levenshtein Distance.
"""
from typing import List, Tuple, Dict, Any


def levenshtein_distance(seq1: List[Any], seq2: List[Any]) -> Tuple[int, int, int, int]:
    """
    Computes Levenshtein edit distance between two sequences (words or characters).
    Returns (distance, substitutions, deletions, insertions).
    """
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    # Backtrack to count operations
    i, j = m, n
    subs, dels, inss = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and seq1[i - 1] == seq2[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dels += 1
            i -= 1
        else:
            inss += 1
            j -= 1

    return dp[m][n], subs, dels, inss


def compute_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    Calculates Word Error Rate (WER):
    WER = (Substitutions + Deletions + Insertions) / Total Reference Words
    """
    ref_words = reference.strip().lower().split()
    hyp_words = hypothesis.strip().lower().split()

    if len(ref_words) == 0:
        return {
            "wer": 0.0 if len(hyp_words) == 0 else 1.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": len(hyp_words),
            "ref_words": 0,
            "hyp_words": len(hyp_words)
        }

    dist, s, d, i = levenshtein_distance(ref_words, hyp_words)
    wer = round(dist / len(ref_words), 4)

    return {
        "wer": wer,
        "edit_distance": dist,
        "substitutions": s,
        "deletions": d,
        "insertions": i,
        "ref_words": len(ref_words),
        "hyp_words": len(hyp_words)
    }


def compute_cer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    Calculates Character Error Rate (CER):
    CER = (Substitutions + Deletions + Insertions) / Total Reference Characters
    """
    ref_chars = list(reference.strip().lower())
    hyp_chars = list(hypothesis.strip().lower())

    if len(ref_chars) == 0:
        return {
            "cer": 0.0 if len(hyp_chars) == 0 else 1.0,
            "ref_chars": 0,
            "hyp_chars": len(hyp_chars)
        }

    dist, s, d, i = levenshtein_distance(ref_chars, hyp_chars)
    cer = round(dist / len(ref_chars), 4)

    return {
        "cer": cer,
        "edit_distance": dist,
        "substitutions": s,
        "deletions": d,
        "insertions": i,
        "ref_chars": len(ref_chars),
        "hyp_chars": len(hyp_chars)
    }
