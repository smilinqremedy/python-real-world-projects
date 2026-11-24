"""
Fraud Evaluation Metrics:
Precision, Recall, F1-Score, PR-AUC (Precision-Recall AUC), ROC-AUC,
and Cost-Matrix Tradeoff Analysis.
"""
from typing import Dict, Any, List, Tuple
import numpy as np


def compute_roc_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """Computes Area Under ROC Curve (ROC-AUC) via trapezoidal integration."""
    thresholds = np.linspace(0.0, 1.0, 101)
    tpr_list, fpr_list = [], []

    P = np.sum(y_true == 1)
    N = np.sum(y_true == 0)
    if P == 0 or N == 0:
        return 0.5

    for th in thresholds:
        y_pred = (y_scores >= th).astype(int)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        tpr_list.append(tp / P)
        fpr_list.append(fp / N)

    # Sort by FPR
    order = np.argsort(fpr_list)
    fpr_sorted = np.array(fpr_list)[order]
    tpr_sorted = np.array(tpr_list)[order]

    return round(float(np.trapezoid(tpr_sorted, fpr_sorted)), 4)


def compute_pr_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Computes Precision-Recall AUC (PR-AUC / Average Precision).
    Essential metric for imbalanced fraud datasets where ROC-AUC yields false optimism.
    """
    thresholds = np.linspace(0.01, 0.99, 50)
    prec_list, rec_list = [], []

    P = np.sum(y_true == 1)
    if P == 0:
        return 0.0

    for th in thresholds:
        y_pred = (y_scores >= th).astype(int)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        prec_list.append(prec)
        rec_list.append(rec)

    # Sort by Recall
    order = np.argsort(rec_list)
    rec_sorted = np.array(rec_list)[order]
    prec_sorted = np.array(prec_list)[order]

    return round(float(np.trapezoid(prec_sorted, rec_sorted)), 4)


def evaluate_fraud_model(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Evaluates fraud classification performance at given decision threshold.
    """
    y_pred = (y_scores >= threshold).astype(int)

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0

    roc_auc = compute_roc_auc(y_true, y_scores)
    pr_auc = compute_pr_auc(y_true, y_scores)

    return {
        "total_transactions": len(y_true),
        "actual_fraud_count": int(np.sum(y_true)),
        "decision_threshold": threshold,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "true_positives_detected": tp,
        "false_positives_customer_friction": fp,
        "false_negatives_missed_fraud": fn,
        "true_negatives_legit_cleared": tn,
        "confusion_matrix": [[tn, fp], [fn, tp]]
    }
