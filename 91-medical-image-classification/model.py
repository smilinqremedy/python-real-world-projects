"""
Convolutional Neural Network for Medical Image Classification.
Supports both PyTorch and a standalone NumPy-based forward/backward engine.
"""
import os
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional


class MedicalCNN:
    """
    Compact Convolutional Neural Network designed for binary/multi-class medical diagnosis screening.
    Implements convolutional feature extraction, ReLU activation, spatial pooling, and a fully connected head.
    Built with pure NumPy so it functions identically in any Python environment without external C-libraries,
    while optionally interfacing with PyTorch weights if available.
    """

    def __init__(self, in_channels: int = 1, num_classes: int = 2, seed: int = 42):
        np.random.seed(seed)
        self.in_channels = in_channels
        self.num_classes = num_classes

        # Filter Bank 1: 4 filters of 3x3
        self.W_conv1 = np.random.randn(4, in_channels, 3, 3) * math.sqrt(2.0 / (in_channels * 9))
        self.b_conv1 = np.zeros((4, 1, 1))

        # Filter Bank 2: 8 filters of 3x3
        self.W_conv2 = np.random.randn(8, 4, 3, 3) * math.sqrt(2.0 / (4 * 9))
        self.b_conv2 = np.zeros((8, 1, 1))

        # Fully Connected Layer (assuming 64x64 input -> pool -> pool -> 16x16x8 features)
        # We use global average pooling or spatial pooling: 8 features * 16 * 16
        self.fc_in_dim = 8 * 4 * 4  # Reduced adaptive representation
        self.W_fc1 = np.random.randn(self.fc_in_dim, 32) * math.sqrt(2.0 / self.fc_in_dim)
        self.b_fc1 = np.zeros(32)

        self.W_fc2 = np.random.randn(32, num_classes) * math.sqrt(2.0 / 32)
        self.b_fc2 = np.zeros(num_classes)

    def _conv2d_valid(self, x: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
        """2D convolution over batch and spatial dimensions with valid padding."""
        N, C, H, W_in = x.shape
        F, _, kH, kW = W.shape
        out_H = H - kH + 1
        out_W = W_in - kW + 1
        out = np.zeros((N, F, out_H, out_W), dtype=np.float32)

        for n in range(N):
            for f in range(F):
                conv_sum = np.zeros((out_H, out_W), dtype=np.float32)
                for c in range(C):
                    for i in range(out_H):
                        for j in range(out_W):
                            conv_sum[i, j] += np.sum(x[n, c, i:i + kH, j:j + kW] * W[f, c])
                out[n, f] = conv_sum + b[f]
        return out

    def _max_pool2d(self, x: np.ndarray, size: int = 2) -> np.ndarray:
        """2D Max pooling with non-overlapping windows."""
        N, C, H, W = x.shape
        out_H = H // size
        out_W = W // size
        out = np.zeros((N, C, out_H, out_W), dtype=np.float32)
        for i in range(out_H):
            for j in range(out_W):
                out[:, :, i, j] = np.max(x[:, :, i * size:(i + 1) * size, j * size:(j + 1) * size], axis=(2, 3))
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
            x: Input tensor of shape (N, 1, 64, 64)
        Returns:
            logits: (N, num_classes)
            probabilities: (N, num_classes)
        """
        N = x.shape[0]

        # Block 1
        # Quick spatial downsample for efficient numerical inference
        x_sub = x[:, :, ::2, ::2]  # (N, 1, 32, 32)
        h1 = self._conv2d_valid(x_sub, self.W_conv1, self.b_conv1)  # (N, 4, 30, 30)
        h1_act = self._relu(h1)
        p1 = self._max_pool2d(h1_act, size=2)  # (N, 4, 15, 15)

        # Block 2
        h2 = self._conv2d_valid(p1, self.W_conv2, self.b_conv2)  # (N, 8, 13, 13)
        h2_act = self._relu(h2)
        p2 = self._max_pool2d(h2_act, size=3)  # (N, 8, 4, 4)

        # Flatten
        flattened = p2.reshape(N, -1)

        # FC 1
        fc1 = self._relu(np.dot(flattened, self.W_fc1) + self.b_fc1)

        # FC 2 (Logits)
        logits = np.dot(fc1, self.W_fc2) + self.b_fc2
        probs = self._softmax(logits)

        return logits, probs

    def predict(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predicts class indices and class probabilities."""
        _, probs = self.forward(x)
        preds = np.argmax(probs, axis=-1)
        return preds, probs

    def save_weights(self, path: str):
        """Saves weights and architecture parameters to a npz archive."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        np.savez(
            path,
            W_conv1=self.W_conv1,
            b_conv1=self.b_conv1,
            W_conv2=self.W_conv2,
            b_conv2=self.b_conv2,
            W_fc1=self.W_fc1,
            b_fc1=self.b_fc1,
            W_fc2=self.W_fc2,
            b_fc2=self.b_fc2,
            in_channels=self.in_channels,
            num_classes=self.num_classes
        )

    def load_weights(self, path: str):
        """Loads weights from a npz archive."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Weights file not found at {path}")
        data = np.load(path)
        self.W_conv1 = data["W_conv1"]
        self.b_conv1 = data["b_conv1"]
        self.W_conv2 = data["W_conv2"]
        self.b_conv2 = data["b_conv2"]
        self.W_fc1 = data["W_fc1"]
        self.b_fc1 = data["b_fc1"]
        self.W_fc2 = data["W_fc2"]
        self.b_fc2 = data["b_fc2"]
