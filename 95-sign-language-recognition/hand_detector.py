"""
Hand Landmark Detection, Feature Normalization, and Synthetic Landmark Ingestion.
Extracts 21 3D hand keypoints (wrist, thumb, index, middle, ring, pinky).
Normalizes coordinates relative to the wrist and scales by palm distance.
"""
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image

# 21 Standard MediaPipe Hand Landmark IDs
LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"
]

# Skeletal joint connection pairs for rendering
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


def normalize_landmarks(raw_landmarks: np.ndarray) -> np.ndarray:
    """
    Normalizes 21 3D landmarks (shape: 21, 3).
    1. Translates coordinates so WRIST (index 0) is at origin (0, 0, 0).
    2. Scales by palm distance (distance from WRIST to MIDDLE_MCP, index 9).
    Returns flattened 63-dimensional feature vector.
    """
    if raw_landmarks.shape != (21, 3):
        raise ValueError(f"Expected landmarks array of shape (21, 3), got {raw_landmarks.shape}")

    coords = raw_landmarks.copy()
    wrist = coords[0, :]
    translated = coords - wrist

    # Palm scale: distance from wrist to middle MCP
    palm_size = float(np.linalg.norm(translated[9, :])) + 1e-7
    scaled = translated / palm_size

    return scaled.flatten().astype(np.float32)


def get_canonical_sign_landmarks(sign_name: str) -> np.ndarray:
    """
    Generates canonical 21-point 3D hand coordinates for supported signs.
    Simulates physical anatomy: WRIST at (0,0,0), MCP joints at palm base,
    and extended or curled PIP/DIP/TIP joints according to sign handshape.
    """
    coords = np.zeros((21, 3), dtype=np.float32)
    # 0: Wrist
    coords[0] = [0.0, 0.0, 0.0]

    # Palm MCP arch
    coords[1] = [-0.25, 0.20, 0.0]   # Thumb CMC
    coords[2] = [-0.35, 0.35, 0.0]   # Thumb MCP
    coords[5] = [-0.18, 0.60, 0.0]   # Index MCP
    coords[9] = [0.0, 0.65, 0.0]     # Middle MCP
    coords[13] = [0.18, 0.60, 0.0]   # Ring MCP
    coords[17] = [0.32, 0.50, 0.0]   # Pinky MCP

    # Helper function to extend finger
    def extend_finger(mcp_idx: int, dir_x: float, dir_y: float):
        base = coords[mcp_idx]
        coords[mcp_idx + 1] = base + np.array([dir_x * 0.25, dir_y * 0.25, 0.0], dtype=np.float32)
        coords[mcp_idx + 2] = coords[mcp_idx + 1] + np.array([dir_x * 0.20, dir_y * 0.20, 0.0], dtype=np.float32)
        coords[mcp_idx + 3] = coords[mcp_idx + 2] + np.array([dir_x * 0.18, dir_y * 0.18, 0.0], dtype=np.float32)

    # Helper function to curl finger into fist
    def curl_finger(mcp_idx: int, dir_x: float):
        base = coords[mcp_idx]
        coords[mcp_idx + 1] = base + np.array([dir_x * 0.12, 0.15, -0.1], dtype=np.float32)
        coords[mcp_idx + 2] = coords[mcp_idx + 1] + np.array([0.0, -0.08, -0.1], dtype=np.float32)
        coords[mcp_idx + 3] = coords[mcp_idx + 2] + np.array([-dir_x * 0.08, -0.12, 0.0], dtype=np.float32)

    # Thumb positions
    def extend_thumb():
        coords[3] = coords[2] + np.array([-0.20, 0.20, 0.0], dtype=np.float32)
        coords[4] = coords[3] + np.array([-0.18, 0.18, 0.0], dtype=np.float32)

    def fold_thumb():
        coords[3] = coords[2] + np.array([0.15, 0.10, -0.05], dtype=np.float32)
        coords[4] = coords[3] + np.array([0.15, 0.0, -0.05], dtype=np.float32)

    if sign_name in ["Hello", "Please", "Thank You"]:
        # All fingers extended
        extend_thumb()
        extend_finger(5, -0.1, 1.0)
        extend_finger(9, 0.0, 1.0)
        extend_finger(13, 0.1, 1.0)
        extend_finger(17, 0.2, 1.0)
    elif sign_name == "Yes":
        # Closed fist
        fold_thumb()
        curl_finger(5, -0.1)
        curl_finger(9, 0.0)
        curl_finger(13, 0.1)
        curl_finger(17, 0.2)
    elif sign_name == "No":
        # Index & Middle extended, ring & pinky curled, thumb touches index
        coords[3] = coords[2] + np.array([0.05, 0.25, 0.0], dtype=np.float32)
        coords[4] = coords[3] + np.array([0.08, 0.15, 0.0], dtype=np.float32)
        extend_finger(5, -0.05, 0.8)
        extend_finger(9, 0.05, 0.8)
        curl_finger(13, 0.1)
        curl_finger(17, 0.2)
    elif sign_name == "I Love You":
        # Thumb, Index, Pinky extended; Middle, Ring curled
        extend_thumb()
        extend_finger(5, -0.1, 1.0)
        curl_finger(9, 0.0)
        curl_finger(13, 0.1)
        extend_finger(17, 0.25, 1.0)
    elif sign_name == "Good":
        # Thumbs up: upright thumb, all other fingers curled into fist
        coords[3] = coords[2] + np.array([-0.05, 0.35, 0.0], dtype=np.float32)
        coords[4] = coords[3] + np.array([-0.02, 0.30, 0.0], dtype=np.float32)
        curl_finger(5, -0.1)
        curl_finger(9, 0.0)
        curl_finger(13, 0.1)
        curl_finger(17, 0.2)
    elif sign_name == "Peace":
        # Index & Middle extended in V-shape, thumb folds over ring/pinky
        fold_thumb()
        extend_finger(5, -0.3, 0.9)
        extend_finger(9, 0.3, 0.9)
        curl_finger(13, 0.1)
        curl_finger(17, 0.2)
    else:
        # Default open hand
        extend_thumb()
        extend_finger(5, -0.1, 1.0)
        extend_finger(9, 0.0, 1.0)
        extend_finger(13, 0.1, 1.0)
        extend_finger(17, 0.2, 1.0)

    return coords


def generate_landmark_dataset(
    samples_per_sign: int = 30,
    noise_level: float = 0.03,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a properly labeled dataset of normalized hand landmark vectors (N, 63)
    and class label indices (N,) across all supported signs with realistic biomechanical noise.
    """
    from sign_dictionary import SUPPORTED_SIGNS

    np.random.seed(seed)
    X_list, y_list = [], []

    for class_idx, sign_name in enumerate(SUPPORTED_SIGNS):
        canonical = get_canonical_sign_landmarks(sign_name)
        for _ in range(samples_per_sign):
            # Apply Gaussian anatomical jitter
            jitter = np.random.normal(0, noise_level, canonical.shape).astype(np.float32)
            # Apply slight rotation
            theta = np.random.uniform(-0.15, 0.15)
            rot = np.array([
                [np.cos(theta), -np.sin(theta), 0],
                [np.sin(theta), np.cos(theta), 0],
                [0, 0, 1]
            ], dtype=np.float32)
            noisy_coords = np.dot(canonical + jitter, rot)

            feat_vec = normalize_landmarks(noisy_coords)
            X_list.append(feat_vec)
            y_list.append(class_idx)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=int)
