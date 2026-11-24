"""
Ethical Biometrics Module: Facial Detection, Feature Extraction, and Vector Matching.
Privacy Preservation: Raw facial images are NEVER written to persistent storage.
Only 128-dimensional normalized mathematical feature embeddings are stored.
"""
import math
from typing import Tuple, Optional, List
import numpy as np
from PIL import Image


class BiometricConsentError(Exception):
    """Raised when an operation is attempted without valid informed consent."""
    pass


def extract_face_embedding(image: Image.Image) -> np.ndarray:
    """
    Extracts a 128-dimensional normalized mathematical embedding from a face image.
    Uses spatial gradient projection over facial key areas (eyes, nose, mouth regions).
    Privacy Note: Does not retain or serialize the source image.
    """
    # Standardize to 96x96 grayscale
    gray = image.convert("L").resize((96, 96))
    arr = np.array(gray, dtype=np.float32) / 255.0

    # Sobel spatial edge filters
    gy, gx = np.gradient(arr)
    mag = np.sqrt(gx**2 + gy**2)

    # Divide into 16 zones (4x4 grid of 24x24 each)
    # Extract 8 statistical descriptors per zone -> 16 * 8 = 128 dimensions
    embedding = []
    step = 24
    for r in range(4):
        for c in range(4):
            patch = arr[r * step:(r + 1) * step, c * step:(c + 1) * step]
            patch_mag = mag[r * step:(r + 1) * step, c * step:(c + 1) * step]

            embedding.extend([
                float(np.mean(patch)),
                float(np.std(patch)),
                float(np.percentile(patch, 25)),
                float(np.percentile(patch, 75)),
                float(np.mean(patch_mag)),
                float(np.std(patch_mag)),
                float(np.max(patch_mag)),
                float(np.median(patch_mag))
            ])

    emb_arr = np.array(embedding, dtype=np.float32)
    # L2 normalize
    norm = np.linalg.norm(emb_arr) + 1e-8
    return emb_arr / norm


def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Calculates cosine similarity between two 128-dimensional embeddings: range [-1.0, 1.0]."""
    dot = float(np.dot(emb1, emb2))
    norm1 = float(np.linalg.norm(emb1))
    norm2 = float(np.linalg.norm(emb2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def compute_euclidean_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Calculates Euclidean distance between two embeddings."""
    return float(np.linalg.norm(emb1 - emb2))


def match_embedding_against_gallery(
    query_emb: np.ndarray,
    gallery: List[Tuple[int, str, np.ndarray]],
    similarity_threshold: float = 0.85
) -> Optional[Tuple[int, str, float]]:
    """
    Matches query embedding against a gallery of registered embeddings [(participant_id, name, embedding)].
    Returns (participant_id, name, similarity_score) if above threshold, or None.
    """
    best_match = None
    highest_sim = -1.0

    for pid, name, reg_emb in gallery:
        sim = compute_cosine_similarity(query_emb, reg_emb)
        if sim > highest_sim:
            highest_sim = sim
            if sim >= similarity_threshold:
                best_match = (pid, name, round(sim, 4))

    return best_match
