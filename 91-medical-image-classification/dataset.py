"""
Dataset ingestion, preprocessing, normalization, and sample generation.
Designed for medical imaging (e.g. Chest X-Ray Normal vs Pneumonia).
"""
import os
import random
import math
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter
import numpy as np


CLASSES = ["Normal", "Pneumonia"]


def validate_image_file(file_path: str) -> bool:
    """Validate that the target file exists, is non-empty, and is a valid readable image."""
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) == 0:
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def preprocess_image(file_path: str, target_size: Tuple[int, int] = (64, 64)) -> np.ndarray:
    """
    Loads, converts to grayscale, resizes, and normalizes image to [0.0, 1.0] with zero mean.
    Returns:
        np.ndarray of shape (1, target_size[0], target_size[1])
    """
    if not validate_image_file(file_path):
        raise ValueError(f"Invalid or unreadable image file: {file_path}")

    with Image.open(file_path) as img:
        img_gray = img.convert("L").resize(target_size, Image.Resampling.BILINEAR)
        arr = np.array(img_gray, dtype=np.float32) / 255.0

    # Channel normalization: (x - mean) / std
    mean = np.mean(arr)
    std = np.std(arr) + 1e-7
    normalized = (arr - mean) / std

    # Add channel dimension: (1, H, W)
    return np.expand_dims(normalized, axis=0)


def generate_sample_medical_dataset(
    output_dir: str,
    samples_per_class: int = 20,
    img_size: Tuple[int, int] = (64, 64),
    seed: int = 42
) -> Dict[str, List[str]]:
    """
    Generates synthetic sample radiographic images with distinctive patterns
    representing Normal lung fields vs Pneumonic consolidations (opacities).
    Libeled strictly for demonstration and unit testing purposes.
    """
    random.seed(seed)
    np.random.seed(seed)
    dataset_records = {"Normal": [], "Pneumonia": []}

    for cls in CLASSES:
        cls_dir = os.path.join(output_dir, cls)
        os.makedirs(cls_dir, exist_ok=True)

        for i in range(samples_per_class):
            img = Image.new("L", img_size, color=25)
            draw = ImageDraw.Draw(img)

            # Draw anatomical thoracic cage boundary
            draw.ellipse([8, 8, img_size[0] - 8, img_size[1] - 8], outline=110, width=2)
            # Spine column shadow
            mid_x = img_size[0] // 2
            draw.line([(mid_x, 8), (mid_x, img_size[1] - 8)], fill=80, width=4)

            # Left and right lung lobes
            draw.ellipse([12, 14, mid_x - 4, img_size[1] - 16], fill=45)
            draw.ellipse([mid_x + 4, 14, img_size[0] - 12, img_size[1] - 16], fill=45)

            if cls == "Pneumonia":
                # Add irregular cloud consolidation / patchy infiltrates
                patch_x = random.randint(14, mid_x - 10) if random.random() > 0.5 else random.randint(mid_x + 6, img_size[0] - 22)
                patch_y = random.randint(20, img_size[1] - 25)
                draw.ellipse([patch_x, patch_y, patch_x + 16, patch_y + 12], fill=180)
                draw.ellipse([patch_x + 2, patch_y + 4, patch_x + 12, patch_y + 10], fill=220)

            # Smooth realistic radiographic gradient
            img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

            file_name = f"{cls.lower()}_{i + 1:03d}.png"
            file_path = os.path.join(cls_dir, file_name)
            img.save(file_path, "PNG")
            dataset_records[cls].append(file_path)

    return dataset_records


def split_dataset(
    dataset_records: Dict[str, List[str]],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[Tuple[str, int]]]:
    """Splits dataset records into stratified train, val, and test subsets."""
    random.seed(seed)
    train_set, val_set, test_set = [], [], []

    for cls_idx, cls in enumerate(CLASSES):
        files = dataset_records.get(cls, []).copy()
        random.shuffle(files)
        n = len(files)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        for f in files[:n_train]:
            train_set.append((f, cls_idx))
        for f in files[n_train:n_train + n_val]:
            val_set.append((f, cls_idx))
        for f in files[n_train + n_val:]:
            test_set.append((f, cls_idx))

    return train_set, val_set, test_set
