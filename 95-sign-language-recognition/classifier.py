"""
Multi-Layer Perceptron (MLP) Landmark Classifier for Sign Language Recognition.
Trained on 63-dimensional normalized hand coordinates.
"""
import os
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from sign_dictionary import SUPPORTED_SIGNS


class SignClassifier:
    def __init__(self, input_dim: int = 63, hidden_dim: int = 48, num_classes: int = len(SUPPORTED_SIGNS), seed: int = 42):
        np.random.seed(seed)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Layer 1
        self.W1 = np.random.randn(input_dim, hidden_dim).astype(np.float32) * math.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim, dtype=np.float32)

        # Layer 2 (Output Logits)
        self.W2 = np.random.randn(hidden_dim, num_classes).astype(np.float32) * math.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(num_classes, dtype=np.float32)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _softmax(self, z: np.ndarray) -> np.ndarray:
        e_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
        return e_z / np.sum(e_z, axis=-1, keepdims=True)

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Forward pass: returns (logits, probabilities)."""
        if x.ndim == 1:
            x = np.expand_dims(x, axis=0)

        h1 = self._relu(np.dot(x, self.W1) + self.b1)
        logits = np.dot(h1, self.W2) + self.b2
        probs = self._softmax(logits)
        return logits, probs

    def predict(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """Predicts sign name, confidence probability, and top-3 candidate rankings."""
        _, probs = self.forward(feature_vector)
        p = probs[0]
        pred_idx = int(np.argmax(p))
        confidence = float(p[pred_idx])

        # Top 3 ranking
        top_indices = np.argsort(p)[::-1][:3]
        top_rankings = [
            {"sign": SUPPORTED_SIGNS[idx], "confidence": round(float(p[idx]), 4)}
            for idx in top_indices
        ]

        return {
            "predicted_class_id": pred_idx,
            "predicted_sign": SUPPORTED_SIGNS[pred_idx],
            "confidence": round(confidence, 4),
            "top_candidates": top_rankings,
            "all_probabilities": {SUPPORTED_SIGNS[i]: round(float(p[i]), 4) for i in range(self.num_classes)}
        }

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 15,
        lr: float = 0.05,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trains the neural network using mini-batch SGD on cross-entropy loss."""
        N = len(y_train)
        losses = []

        for ep in range(epochs):
            perm = np.random.permutation(N)
            epoch_loss = 0.0

            for idx in perm:
                x_i = X_train[idx:idx + 1]
                y_i = y_train[idx]

                h1_raw = np.dot(x_i, self.W1) + self.b1
                h1 = self._relu(h1_raw)
                logits = np.dot(h1, self.W2) + self.b2
                probs = self._softmax(logits)

                loss = -math.log(max(probs[0, y_i], 1e-7))
                epoch_loss += loss

                # Backprop
                d_logits = probs.copy()
                d_logits[0, y_i] -= 1.0

                dW2 = np.dot(h1.T, d_logits)
                db2 = d_logits[0]

                dh1 = np.dot(d_logits, self.W2.T)
                dh1[h1_raw <= 0] = 0.0  # ReLU gradient

                dW1 = np.dot(x_i.T, dh1)
                db1 = dh1[0]

                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W1 -= lr * dW1
                self.b1 -= lr * db1

            losses.append(round(epoch_loss / N, 4))

        if save_path:
            self.save_weights(save_path)

        return {"epochs": epochs, "final_loss": losses[-1], "loss_history": losses}

    def save_weights(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        np.savez(path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2)

    def load_weights(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Weights file not found at {path}")
        data = np.load(path)
        self.W1 = data["W1"]
        self.b1 = data["b1"]
        self.W2 = data["W2"]
        self.b2 = data["b2"]
