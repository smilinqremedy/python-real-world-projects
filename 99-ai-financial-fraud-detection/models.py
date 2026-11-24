"""
Supervised and Unsupervised Fraud Detection Models & Risk Scoring.
- Supervised: Weighted-Loss Neural Classifier (handles extreme class imbalance).
- Unsupervised: Isolation Forest Anomaly Detector (measures isolation depth).
- Risk Scoring Engine: Calibrates probabilities into 0-100 actionable risk tiers.
"""
import os
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional, List


class SupervisedFraudClassifier:
    """
    Neural Decision Boundary trained with class-weighted cross-entropy loss
    to prevent majority-class collapse on imbalanced fraud datasets.
    """
    def __init__(self, input_dim: int = 10, hidden_dim: int = 32, fraud_weight: float = 25.0, seed: int = 42):
        np.random.seed(seed)
        self.fraud_weight = fraud_weight

        # Weights
        self.W1 = np.random.randn(input_dim, hidden_dim).astype(np.float32) * math.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim, dtype=np.float32)

        self.W2 = np.random.randn(hidden_dim, 1).astype(np.float32) * math.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(1, dtype=np.float32)

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -15.0, 15.0)))

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def forward(self, x: np.ndarray) -> np.ndarray:
        h1 = self._relu(np.dot(x, self.W1) + self.b1)
        logits = np.dot(h1, self.W2) + self.b2
        return self._sigmoid(logits).flatten()

    def train(self, X_train: np.ndarray, y_train: np.ndarray, epochs: int = 25, lr: float = 0.03):
        N = len(y_train)
        for ep in range(epochs):
            perm = np.random.permutation(N)
            for idx in perm:
                x_i = X_train[idx:idx + 1]
                y_i = float(y_train[idx])

                h1_raw = np.dot(x_i, self.W1) + self.b1
                h1 = self._relu(h1_raw)
                logit = np.dot(h1, self.W2) + self.b2
                p = float(self._sigmoid(logit)[0, 0])

                # Weighted gradient: scale error when ground truth is fraud
                weight = self.fraud_weight if y_i == 1.0 else 1.0
                grad_logit = weight * (p - y_i)

                dW2 = h1.T * grad_logit
                db2 = grad_logit

                dh1 = grad_logit * self.W2.T
                dh1[h1_raw <= 0] = 0.0

                dW1 = np.dot(x_i.T, dh1)
                db1 = dh1[0]

                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W1 -= lr * dW1
                self.b1 -= lr * db1


class IsolationForestAnomalyDetector:
    """
    Unsupervised Isolation Forest:
    Isolates observations by randomly selecting a feature and splitting value.
    Anomalous transactions require fewer partitions (shorter path lengths) to isolate.
    """
    def __init__(self, n_trees: int = 15, max_depth: int = 8, seed: int = 42):
        np.random.seed(seed)
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.trees: List[Dict[str, Any]] = []

    def _build_tree(self, X: np.ndarray, depth: int) -> Dict[str, Any]:
        N, D = X.shape
        if depth >= self.max_depth or N <= 2:
            return {"type": "leaf", "size": N}

        feat_idx = np.random.randint(0, D)
        f_min, f_max = float(np.min(X[:, feat_idx])), float(np.max(X[:, feat_idx]))
        if f_min == f_max:
            return {"type": "leaf", "size": N}

        split_val = np.random.uniform(f_min, f_max)
        left_mask = X[:, feat_idx] < split_val

        return {
            "type": "split",
            "feature": feat_idx,
            "split_val": split_val,
            "left": self._build_tree(X[left_mask], depth + 1),
            "right": self._build_tree(X[~left_mask], depth + 1)
        }

    def fit(self, X: np.ndarray):
        self.trees = [self._build_tree(X, depth=0) for _ in range(self.n_trees)]

    def _path_length(self, x: np.ndarray, node: Dict[str, Any], depth: int) -> float:
        if node["type"] == "leaf":
            return depth + (0.5 if node["size"] > 1 else 0.0)

        feat = node["feature"]
        if x[feat] < node["split_val"]:
            return self._path_length(x, node["left"], depth + 1)
        else:
            return self._path_length(x, node["right"], depth + 1)

    def score_anomalies(self, X: np.ndarray) -> np.ndarray:
        """
        Computes anomaly score in range [0.0, 1.0].
        Scores close to 1.0 represent strong outliers (anomalies).
        """
        N = len(X)
        scores = np.zeros(N, dtype=np.float32)
        c = self.max_depth * 0.7

        for i in range(N):
            lengths = [self._path_length(X[i], t, depth=0) for t in self.trees]
            avg_length = np.mean(lengths)
            # Anomaly score formula: 2^(-avg_length / c)
            score = 2.0 ** (-avg_length / max(1.0, c))
            scores[i] = score

        return scores


def calculate_risk_score(supervised_prob: float, anomaly_score: float) -> Tuple[float, str, str]:
    """
    Blends supervised fraud probability (70% weight) and unsupervised anomaly score (30% weight).
    Returns (risk_score_0_100, risk_tier, recommended_action).
    """
    blended = 0.70 * supervised_prob + 0.30 * anomaly_score
    risk_score = round(min(100.0, max(0.0, blended * 100.0)), 1)

    if risk_score <= 30.0:
        return risk_score, "LOW", "Approve Transaction"
    elif risk_score <= 70.0:
        return risk_score, "MODERATE", "Trigger Step-Up MFA / Identity Verification"
    else:
        return risk_score, "HIGH", "Flag for Fraud Analyst Review (Do NOT Auto-Block)"
