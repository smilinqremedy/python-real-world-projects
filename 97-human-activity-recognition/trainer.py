"""
Model Training Pipeline for Human Activity Recognition (1D-CNN).
Trains the neural network on windowed sensor sequences with mini-batch SGD,
tracks validation loss, and checkpoints weights.
"""
import os
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from model import HAR1DCNN
from evaluator import HAREvaluator


class HARTrainer:
    def __init__(self, model: Optional[HAR1DCNN] = None):
        self.model = model or HAR1DCNN(in_channels=6, window_size=64)
        self.history = {"train_loss": [], "val_accuracy": [], "val_f1": []}

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 6,
        lr: float = 0.02,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trains the 1D-CNN model on input (N, 6, 64) and evaluates on validation set.
        """
        N = len(y_train)
        if N == 0:
            raise ValueError("Training dataset cannot be empty.")

        for ep in range(epochs):
            perm = np.random.permutation(N)
            epoch_loss = 0.0

            for idx in perm:
                x_i = X_train[idx:idx + 1]
                y_i = y_train[idx]

                logits, probs = self.model.forward(x_i)
                loss = -math.log(max(probs[0, y_i], 1e-7))
                epoch_loss += loss

                # Backprop to final FC layer
                grad_logits = probs.copy()
                grad_logits[0, y_i] -= 1.0

                # Feature representation after Conv+Pool layers
                h1 = self.model._relu(self.model._conv1d(x_i, self.model.W_conv1, self.model.b_conv1))
                p1 = self.model._max_pool1d(h1, size=2)
                h2 = self.model._relu(self.model._conv1d(p1, self.model.W_conv2, self.model.b_conv2))
                p2 = self.model._max_pool1d(h2, size=2)
                flat = p2.reshape(1, -1)

                grad_W_fc = np.dot(flat.T, grad_logits)
                grad_b_fc = grad_logits[0]

                self.model.W_fc -= lr * grad_W_fc
                self.model.b_fc -= lr * grad_b_fc

            avg_loss = epoch_loss / N
            self.history["train_loss"].append(round(avg_loss, 4))

            # Validation check
            if X_val is not None and y_val is not None and len(y_val) > 0:
                preds, _ = self.model.predict(X_val)
                metrics = HAREvaluator.evaluate(y_val, preds)
                self.history["val_accuracy"].append(metrics.get("accuracy", 0.0))
                self.history["val_f1"].append(metrics.get("macro_f1", 0.0))

        if save_path:
            self.model.save_weights(save_path)

        final_val = HAREvaluator.evaluate(y_val, self.model.predict(X_val)[0]) if (X_val is not None and len(y_val) > 0) else {}

        return {
            "epochs": epochs,
            "final_train_loss": self.history["train_loss"][-1],
            "validation_metrics": final_val,
            "weights_saved_to": save_path
        }
