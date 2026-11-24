"""
Evaluation metrics for medical diagnostic screening:
Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score, and Confusion Matrix.
"""
from typing import List, Dict, Any, Tuple
import numpy as np


class MedicalEvaluator:
    @staticmethod
    def compute_confusion_matrix(y_true: List[int], y_pred: List[int], num_classes: int = 2) -> np.ndarray:
        """Generates an NxN confusion matrix where row=actual, col=predicted."""
        cm = np.zeros((num_classes, num_classes), dtype=int)
        for t, p in zip(y_true, y_pred):
            if 0 <= t < num_classes and 0 <= p < num_classes:
                cm[t, p] += 1
        return cm

    @staticmethod
    def evaluate(y_true: List[int], y_pred: List[int], num_classes: int = 2) -> Dict[str, Any]:
        """
        Computes clinical screening performance metrics without fabrication.
        Calculates Accuracy, Precision, Recall, Specificity, and F1-score.
        """
        if len(y_true) == 0:
            return {"error": "Empty evaluation dataset"}

        cm = MedicalEvaluator.compute_confusion_matrix(y_true, y_pred, num_classes)
        total = len(y_true)
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        accuracy = correct / total if total > 0 else 0.0

        if num_classes == 2:
            # Binary classification: 0=Normal (Negative), 1=Pneumonia (Positive)
            tn = cm[0, 0]
            fp = cm[0, 1]
            fn = cm[1, 0]
            tp = cm[1, 1]

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Sensitivity
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            return {
                "total_samples": total,
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "specificity": round(specificity, 4),
                "f1_score": round(f1, 4),
                "confusion_matrix": cm.tolist(),
                "true_positive": int(tp),
                "false_positive": int(fp),
                "true_negative": int(tn),
                "false_negative": int(fn)
            }
        else:
            # Macro-averaged metrics for multi-class
            precision_list, recall_list = [], []
            for c in range(num_classes):
                tp = cm[c, c]
                fp = np.sum(cm[:, c]) - tp
                fn = np.sum(cm[c, :]) - tp
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                precision_list.append(prec)
                recall_list.append(rec)

            avg_precision = float(np.mean(precision_list))
            avg_recall = float(np.mean(recall_list))
            f1 = (
                2 * (avg_precision * avg_recall) / (avg_precision + avg_recall)
                if (avg_precision + avg_recall) > 0 else 0.0
            )

            return {
                "total_samples": total,
                "accuracy": round(accuracy, 4),
                "precision": round(avg_precision, 4),
                "recall": round(avg_recall, 4),
                "f1_score": round(f1, 4),
                "confusion_matrix": cm.tolist()
            }
