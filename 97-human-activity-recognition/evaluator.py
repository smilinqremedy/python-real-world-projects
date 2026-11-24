"""
Human Activity Recognition Evaluator:
Calculates multi-class Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
"""
from typing import Dict, Any, List
import numpy as np
from dataset import ACTIVITIES


class HAREvaluator:
    @staticmethod
    def evaluate(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = len(ACTIVITIES)) -> Dict[str, Any]:
        """Calculates multi-class classification metrics."""
        total = len(y_true)
        if total == 0:
            return {"error": "Empty evaluation dataset"}

        cm = np.zeros((num_classes, num_classes), dtype=int)
        for t, p in zip(y_true, y_pred):
            if 0 <= t < num_classes and 0 <= p < num_classes:
                cm[t, p] += 1

        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        accuracy = correct / total

        precisions, recalls, f1s = [], [], []
        per_class = {}

        for c in range(num_classes):
            tp = cm[c, c]
            fp = np.sum(cm[:, c]) - tp
            fn = np.sum(cm[c, :]) - tp

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

            per_class[ACTIVITIES[c]] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "samples": int(np.sum(cm[c, :]))
            }

        return {
            "total_samples": total,
            "accuracy": round(accuracy, 4),
            "macro_precision": round(float(np.mean(precisions)), 4),
            "macro_recall": round(float(np.mean(recalls)), 4),
            "macro_f1": round(float(np.mean(f1s)), 4),
            "per_class": per_class,
            "confusion_matrix": cm.tolist()
        }
