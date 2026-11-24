"""
Evaluation metrics for Sign Language Gesture Classification.
Computes multi-class Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
"""
from typing import List, Dict, Any
import numpy as np
from sign_dictionary import SUPPORTED_SIGNS


class SignEvaluator:
    @staticmethod
    def evaluate(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = len(SUPPORTED_SIGNS)) -> Dict[str, Any]:
        """Calculates multi-class classification metrics."""
        total = len(y_true)
        if total == 0:
            return {"error": "Empty test dataset"}

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

            sign_name = SUPPORTED_SIGNS[c]
            per_class[sign_name] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "samples": int(np.sum(cm[c, :]))
            }

        macro_precision = float(np.mean(precisions))
        macro_recall = float(np.mean(recalls))
        macro_f1 = float(np.mean(f1s))

        return {
            "total_samples": total,
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class": per_class,
            "confusion_matrix": cm.tolist()
        }
