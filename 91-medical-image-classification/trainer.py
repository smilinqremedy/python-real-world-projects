"""
Model Trainer for Medical Image Classification.
Trains the MedicalCNN using backpropagation or feature-based optimization,
evaluating on validation splits and checkpointing weights.
"""
import os
import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataset import preprocess_image, split_dataset, CLASSES
from model import MedicalCNN
from evaluator import MedicalEvaluator


class MedicalModelTrainer:
    def __init__(self, model: Optional[MedicalCNN] = None):
        self.model = model or MedicalCNN(in_channels=1, num_classes=2)
        self.history = {"train_loss": [], "val_accuracy": [], "val_f1": []}

    def train(
        self,
        train_data: List[Tuple[str, int]],
        val_data: List[Tuple[str, int]],
        epochs: int = 5,
        learning_rate: float = 0.01,
        save_weights_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trains the neural network on train_data and tracks validation metrics.
        """
        if len(train_data) == 0:
            raise ValueError("Training dataset is empty.")

        # Load and preprocess all training samples
        X_train_list, y_train_list = [], []
        for path, label in train_data:
            try:
                arr = preprocess_image(path)
                X_train_list.append(arr)
                y_train_list.append(label)
            except Exception as e:
                continue

        if not X_train_list:
            raise RuntimeError("No valid images could be loaded for training.")

        X_train = np.stack(X_train_list, axis=0)  # (N, 1, 64, 64)
        y_train = np.array(y_train_list, dtype=int)
        N = len(y_train)

        # Numerical training loop (stochastic mini-batch optimization on final projection)
        for epoch in range(1, epochs + 1):
            perm = np.random.permutation(N)
            epoch_loss = 0.0

            for idx in perm:
                sample_x = X_train[idx:idx + 1]
                target_y = y_train[idx]

                logits, probs = self.model.forward(sample_x)
                # Cross entropy loss
                p_correct = max(probs[0, target_y], 1e-7)
                loss = -math.log(p_correct)
                epoch_loss += loss

                # Gradient with respect to logits: p - 1 for target, p otherwise
                grad_logits = probs.copy()
                grad_logits[0, target_y] -= 1.0

                # Backprop to W_fc2 and b_fc2
                # h_fc1 from forward
                x_sub = sample_x[:, :, ::2, ::2]
                h1 = self.model._relu(self.model._conv2d_valid(x_sub, self.model.W_conv1, self.model.b_conv1))
                p1 = self.model._max_pool2d(h1, size=2)
                h2 = self.model._relu(self.model._conv2d_valid(p1, self.model.W_conv2, self.model.b_conv2))
                p2 = self.model._max_pool2d(h2, size=3)
                flat = p2.reshape(1, -1)
                fc1 = self.model._relu(np.dot(flat, self.model.W_fc1) + self.model.b_fc1)

                grad_W_fc2 = np.dot(fc1.T, grad_logits)
                grad_b_fc2 = grad_logits[0]

                # Update weights
                self.model.W_fc2 -= learning_rate * grad_W_fc2
                self.model.b_fc2 -= learning_rate * grad_b_fc2

            avg_loss = epoch_loss / N
            self.history["train_loss"].append(round(avg_loss, 4))

            # Validation check
            if val_data:
                val_eval = self.evaluate(val_data)
                self.history["val_accuracy"].append(val_eval.get("accuracy", 0.0))
                self.history["val_f1"].append(val_eval.get("f1_score", 0.0))

        if save_weights_path:
            self.model.save_weights(save_weights_path)

        final_eval = self.evaluate(val_data) if val_data else {}
        return {
            "epochs": epochs,
            "final_train_loss": self.history["train_loss"][-1] if self.history["train_loss"] else 0.0,
            "validation_metrics": final_eval,
            "weights_saved_to": save_weights_path
        }

    def evaluate(self, eval_data: List[Tuple[str, int]]) -> Dict[str, Any]:
        """Evaluates the model over the provided dataset split."""
        y_true, y_pred = [], []
        for path, label in eval_data:
            try:
                arr = preprocess_image(path)
                if arr.ndim == 3:
                    arr = np.expand_dims(arr, axis=0)
                pred, _ = self.model.predict(arr)
                y_true.append(label)
                y_pred.append(int(pred[0]))
            except Exception:
                continue

        return MedicalEvaluator.evaluate(y_true, y_pred, num_classes=self.model.num_classes)
