"""
Dataset Ingestion, Synthetic Transaction Generation, and Preprocessing.
Models realistic financial transactions with extreme class imbalance (e.g. 1-3% fraud).
Applies RobustScaler (median and interquartile range) to handle severe financial outliers.
"""
import os
import csv
import math
import numpy as np
from typing import Tuple, Dict, Any, List, Optional

FEATURE_NAMES = [
    "amount", "time_step", "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"
]


def generate_synthetic_transactions(
    output_csv: Optional[str] = None,
    n_samples: int = 1200,
    fraud_ratio: float = 0.03,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Generates realistic synthetic credit card / banking transactions with extreme class imbalance.
    Fraudulent transactions display anomalous amounts, unusual time intervals, and shifted PCA vectors.
    """
    np.random.seed(seed)
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud

    # 1. Legitimate transactions
    # Amounts follow log-normal distribution centered around $45 (typical consumer purchases)
    legit_amounts = np.random.lognormal(mean=3.8, sigma=0.8, size=n_legit)
    legit_time = np.sort(np.random.uniform(0, 86400, size=n_legit))  # Seconds in a day
    # PCA latent features centered at 0 with standard variance
    legit_pca = np.random.normal(0, 1.0, size=(n_legit, 8))

    X_legit = np.column_stack([legit_amounts, legit_time, legit_pca])
    y_legit = np.zeros(n_legit, dtype=int)

    # 2. Fraudulent transactions
    # Fraud amounts: bifurcated into either micro-testing ($1.50) or massive drain attempts ($2500+)
    fraud_amounts = []
    for _ in range(n_fraud):
        if np.random.random() > 0.4:
            fraud_amounts.append(np.random.uniform(1200.0, 4800.0))
        else:
            fraud_amounts.append(np.random.uniform(1.0, 4.0))
    fraud_amounts = np.array(fraud_amounts)

    # Fraud bursts occurring during unusual late-night hours (e.g. 1 AM - 4 AM = 3600s - 14400s)
    fraud_time = np.random.uniform(3600, 14400, size=n_fraud)
    # Fraud PCA vectors exhibit negative drift on V1/V2 and sharp spikes on V3/V4
    fraud_pca = np.random.normal(0, 1.5, size=(n_fraud, 8))
    fraud_pca[:, 0] -= 2.8  # v1 strong negative shift
    fraud_pca[:, 1] += 2.2  # v2 positive shift
    fraud_pca[:, 2] -= 2.0  # v3 negative shift

    X_fraud = np.column_stack([fraud_amounts, fraud_time, fraud_pca])
    y_fraud = np.ones(n_fraud, dtype=int)

    # Combine and shuffle
    X = np.vstack([X_legit, X_fraud]).astype(np.float32)
    y = np.concatenate([y_legit, y_fraud]).astype(int)

    perm = np.random.permutation(n_samples)
    X = X[perm]
    y = y[perm]

    tx_ids = [f"TXN-{100000 + i}" for i in range(n_samples)]

    if output_csv:
        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["transaction_id"] + FEATURE_NAMES + ["is_fraud"])
            for i in range(n_samples):
                row = [tx_ids[i]] + [round(float(v), 4) for v in X[i]] + [int(y[i])]
                writer.writerow(row)

    return X, y, tx_ids


def robust_scale(X: np.ndarray, medians: Optional[np.ndarray] = None, iqrs: Optional[np.ndarray] = None):
    """
    Applies RobustScaler: (x - median) / IQR.
    Resistant to extreme statistical outliers in financial transaction amounts.
    """
    if medians is None:
        medians = np.median(X, axis=0)
    if iqrs is None:
        q75 = np.percentile(X, 75, axis=0)
        q25 = np.percentile(X, 25, axis=0)
        iqrs = q75 - q25
        iqrs[iqrs == 0.0] = 1.0  # Prevent divide-by-zero

    scaled = (X - medians) / iqrs
    return scaled.astype(np.float32), medians, iqrs


def stratified_split(
    X: np.ndarray,
    y: np.ndarray,
    test_ratio: float = 0.25,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Stratified splitting ensuring identical minority fraud ratio in train and test splits."""
    np.random.seed(seed)
    idx_0 = np.where(y == 0)[0]
    idx_1 = np.where(y == 1)[0]

    np.random.shuffle(idx_0)
    np.random.shuffle(idx_1)

    n_test_0 = int(len(idx_0) * test_ratio)
    n_test_1 = int(len(idx_1) * test_ratio)

    test_idx = np.concatenate([idx_0[:n_test_0], idx_1[:n_test_1]])
    train_idx = np.concatenate([idx_0[n_test_0:], idx_1[n_test_1:]])

    np.random.shuffle(train_idx)
    np.random.shuffle(test_idx)

    return X[train_idx], y[train_idx], X[test_idx], y[test_idx]
