"""
1D Convolutional Neural Network (1D-CNN) for Human Activity Recognition.
Designed for 6-channel inertial sequences: (N, 6, window_size).
Implements 1D temporal filtering, max pooling, and dense classification.
"""
import os
import math
import numpy as np
from typing import Tuple, Dict, Any, Optional
from dataset import ACTIVITIES


class HAR1DCNN:
    def __init__(
        self,
        in_channels: int = 6,
        window_size: int = 64,
        num_classes: int = len(ACTIVITIES),
        seed: int = 42
    ):
        np.random.seed(seed)
        self.in_channels = in_channels
        self.window_size = window_size
        self.num_classes = num_classes

        # Conv1: 8 filters of kernel size 5
        # Output: (N, 8, 60) -> Pool / 2 -> (N, 8, 30)
        self.W_conv1 = np.random.randn(8, in_channels, 5).astype(np.float32) * math.sqrt(2.0 / (in_channels * 5))
        self.b_conv1 = np.zeros((8, 1), dtype=np.float32)

        # Conv2: 16 filters of kernel size 5
        # Input (N, 8, 30) -> Output: (N, 16, 26) -> Pool / 2 -> (N, 16, 13)
        self.W_conv2 = np.random.randn(16, 8, 5).astype(np.float32) * math.sqrt(2.0 / (8 * 5))
        self.b_conv2 = np.zeros((16, 1), dtype=np.float32)

        # Flatten dimension: 16 * 13 = 208
        self.fc_dim = 16 * 13
        self.W_fc = np.random.randn(self.fc_dim, num_classes).astype(np.float32) * math.sqrt(2.0 / self.fc_dim)
        self.b_fc = np.zeros(num_classes, dtype=np.float32)

    def _conv1d(self, x: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
        """1D convolution over temporal dimension with valid padding."""
        N, C, L = x.shape
        F, _, K = W.shape
        out_L = L - K + 1
        out = np.zeros((N, F, out_L), dtype=np.float32)

        for n in range(N):
            for f in range(F):
                conv_sum = np.zeros(out_L, dtype=np.float32)
                for c in range(C):
                    for i in range(out_L):
                        conv_sum[i] += np.sum(x[n, c, i:i + K] * W[f, c])
                out[n, f] = conv_sum + b[f, 0]
        return out

    def _max_pool1d(self, x: np.ndarray, size: int = 2) -> np.ndarray:
        N, C, L = x.shape
        out_L = L // size
        out = np.zeros((N, C, out_L), dtype=np.float32)
        for i in range(out_L):
            out[:, :, i] = np.max(x[:, :, i * size:(i + 1) * size], axis=2)
        return out

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _softmax(self, z: np.ndarray) -> np.ndarray:
        e_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
        return e_z / np.sum(e_z, axis=-1, keepdims=True)

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass.
        Args:
            x: Input of shape (N, 6, 64)
        Returns:
            logits: (N, 6)
            probabilities: (N, 6)
        """
        if x.ndim == 2:
            x = np.expand_dims(x, axis=0)

        N = x.shape[0]
        # Conv block 1
        h1 = self._relu(self._conv1d(x, self.W_conv1, self.b_conv1))
        p1 = self._max_pool1d(h1, size=2)

        # Conv block 2
        h2 = self._relu(self._conv1d(p1, self.W_conv2, self.b_conv2))
        p2 = self._max_pool1d(h2, size=2)

        # Flatten & FC classification head
        flat = p2.reshape(N, -1)
        logits = np.dot(flat, self.W_fc) + self.b_fc
        probs = self._softmax(logits)

        return logits, probs

    def predict(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        _, probs = self.forward(x)
        preds = np.argmax(probs, axis=-1)
        return preds, probs

    def save_weights(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        np.savez(
            path,
            W_conv1=self.W_conv1,
            b_conv1=self.b_conv1,
            W_conv2=self.W_conv2,
            b_conv2=self.b_conv2,
            W_fc=self.W_fc,
            b_fc=self.b_fc
        )

    def load_weights(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Weights file not found at {path}")
        data = np.load(path)
        self.W_conv1 = data["W_conv1"]
        self.b_conv1 = data["b_conv1"]
        self.W_conv2 = data["W_conv2"]
        self.b_conv2 = data["b_conv2"]
        self.W_fc = data["W_fc"]
        self.b_fc = data["b_fc"]
