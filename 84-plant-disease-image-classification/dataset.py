"""
Plant Leaf Image Dataset Generator & Augmentation Pipeline.
Generates synthetic 64x64 RGB plant leaf samples across 5 disease categories with visual lesions.
"""
import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader


DISEASE_CLASSES = [
    "Healthy Leaf",
    "Bacterial Blight",
    "Early Blight",
    "Powdery Mildew",
    "Leaf Rust"
]
CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(DISEASE_CLASSES)}
IDX_TO_CLASS = {i: cls_name for i, cls_name in enumerate(DISEASE_CLASSES)}


def synthesize_leaf_image(disease_category: str, seed: int = None) -> np.ndarray:
    """
    Synthesizes a 64x64x3 RGB image of a plant leaf with category-specific pathology:
    - Base: Green leaf ellipse with central and lateral veins.
    - Pathologies:
      - Healthy Leaf: Clean rich green tones.
      - Bacterial Blight: Irregular dark brown/black water-soaked lesions with yellowish halos.
      - Early Blight: Dark brown concentric circular lesions (target board pattern).
      - Powdery Mildew: White powdery fungal patches across the surface.
      - Leaf Rust: Small reddish-brown/orange raised pustules.
    """
    if seed is not None:
        np.random.seed(seed)

    # Background (soil / bench light gray)
    img = np.full((64, 64, 3), 45, dtype=np.uint8)

    # Leaf blade contour: Green ellipse
    cv2.ellipse(img, (32, 32), (18, 28), 0, 0, 360, (35, 140, 50), -1)

    # Primary vein
    cv2.line(img, (32, 6), (32, 58), (55, 175, 75), 1)
    # Secondary lateral veins
    for y_pos in range(16, 50, 7):
        cv2.line(img, (32, y_pos), (20, y_pos - 4), (45, 160, 65), 1)
        cv2.line(img, (32, y_pos), (44, y_pos - 4), (45, 160, 65), 1)

    # Add pathology signatures
    if disease_category == "Bacterial Blight":
        # Dark brown water-soaked blotches with yellow halos
        for center in [(26, 24), (36, 40), (28, 46)]:
            cv2.circle(img, center, 6, (40, 190, 200), -1)  # Yellow halo (BGR)
            cv2.circle(img, center, 4, (15, 25, 60), -1)    # Dark water-soaked core
    elif disease_category == "Early Blight":
        # Concentric brown rings
        for center in [(25, 30), (38, 26), (32, 44)]:
            cv2.circle(img, center, 6, (20, 45, 110), 1)
            cv2.circle(img, center, 4, (20, 45, 110), 1)
            cv2.circle(img, center, 2, (15, 35, 80), -1)
    elif disease_category == "Powdery Mildew":
        # White powdery fungal blotches
        for center in [(27, 22), (37, 34), (25, 42), (35, 20)]:
            cv2.circle(img, center, 5, (220, 230, 235), -1)
    elif disease_category == "Leaf Rust":
        # Reddish-orange pustules
        for center in [(24, 20), (38, 25), (28, 35), (36, 42), (24, 48), (34, 50)]:
            cv2.circle(img, center, 2, (10, 70, 200), -1)

    # Add subtle sensor noise
    noise = np.random.normal(0, 5, (64, 64, 3)).astype(np.int16)
    noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy_img


def apply_augmentation(img: np.ndarray) -> np.ndarray:
    """
    Applies image augmentation: random flip, rotation, and slight brightness jitter.
    """
    augmented = img.copy()
    # Random horizontal flip
    if np.random.rand() > 0.5:
        augmented = cv2.flip(augmented, 1)
    # Random vertical flip
    if np.random.rand() > 0.5:
        augmented = cv2.flip(augmented, 0)
    # Random rotation
    angle = np.random.choice([0, 90, 180, 270])
    if angle == 90:
        augmented = cv2.rotate(augmented, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        augmented = cv2.rotate(augmented, cv2.ROTATE_180)
    elif angle == 270:
        augmented = cv2.rotate(augmented, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Slight brightness jitter
    jitter = np.random.randint(-15, 15)
    augmented = np.clip(augmented.astype(np.int16) + jitter, 0, 255).astype(np.uint8)
    return augmented


class PlantLeafDataset(Dataset):
    def __init__(self, images: np.ndarray, labels: np.ndarray, augment: bool = False):
        self.images = images
        self.labels = labels
        self.augment = augment

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        img = self.images[idx]
        if self.augment:
            img = apply_augmentation(img)

        # Convert HWC (BGR/RGB) to CHW, normalize to [0, 1]
        tensor_img = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return tensor_img, label


def create_plant_dataloaders(samples_per_class: int = 100, batch_size: int = 32, seed: int = 42):
    np.random.seed(seed)
    images = []
    labels = []

    for label_idx, disease in enumerate(DISEASE_CLASSES):
        for s in range(samples_per_class):
            img = synthesize_leaf_image(disease, seed=seed * 1000 + label_idx * 500 + s)
            images.append(img)
            labels.append(label_idx)

    images = np.array(images)
    labels = np.array(labels)

    indices = np.random.permutation(len(labels))
    images = images[indices]
    labels = labels[indices]

    split = int(0.8 * len(labels))
    train_imgs, test_imgs = images[:split], images[split:]
    train_lbls, test_lbls = labels[:split], labels[split:]

    train_ds = PlantLeafDataset(train_imgs, train_lbls, augment=True)
    test_ds = PlantLeafDataset(test_imgs, test_lbls, augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader, test_imgs, test_lbls
