"""
Dataset Generation and Preprocessing for Facial Expression Recognition.
Generates reproducible synthetic 48x48 facial expression images with distinct visual features.
"""
import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader


EXPRESSION_CLASSES = ["Angry", "Happy", "Neutral", "Sad", "Surprise"]
CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(EXPRESSION_CLASSES)}
IDX_TO_CLASS = {i: cls_name for i, cls_name in enumerate(EXPRESSION_CLASSES)}


def synthesize_face_image(expression: str, seed: int = None) -> np.ndarray:
    """
    Synthesizes a 48x48 single-channel face avatar with expression-specific geometry:
    - Eyes and eyebrows
    - Mouth (smile, frown, open O, straight line, angled)
    """
    if seed is not None:
        np.random.seed(seed)

    img = np.full((48, 48), 190, dtype=np.uint8)

    # Face contour (oval)
    cv2.ellipse(img, (24, 24), (18, 22), 0, 0, 360, 220, -1)
    cv2.ellipse(img, (24, 24), (18, 22), 0, 0, 360, 50, 1)

    # Eyes
    cv2.circle(img, (17, 18), 3, 40, -1)
    cv2.circle(img, (31, 18), 3, 40, -1)

    # Eyebrows & Mouth per expression
    if expression == "Happy":
        # Eyebrows: arched
        cv2.line(img, (14, 13), (20, 13), 30, 1)
        cv2.line(img, (28, 13), (34, 13), 30, 1)
        # Upward curved mouth (smile)
        cv2.ellipse(img, (24, 31), (9, 6), 0, 0, 180, 30, 2)
    elif expression == "Sad":
        # Eyebrows: inner edges raised
        cv2.line(img, (14, 15), (20, 12), 30, 1)
        cv2.line(img, (28, 12), (34, 15), 30, 1)
        # Downward curved mouth (frown)
        cv2.ellipse(img, (24, 38), (8, 5), 0, 180, 360, 30, 2)
    elif expression == "Surprise":
        # Raised high eyebrows
        cv2.line(img, (14, 11), (20, 11), 30, 1)
        cv2.line(img, (28, 11), (34, 11), 30, 1)
        # Wide open round mouth
        cv2.circle(img, (24, 34), 5, 30, 2)
    elif expression == "Angry":
        # Slanted downward furrowed eyebrows
        cv2.line(img, (14, 12), (20, 16), 30, 2)
        cv2.line(img, (28, 16), (34, 12), 30, 2)
        # Tightly clamped straight mouth
        cv2.line(img, (17, 34), (31, 34), 30, 2)
    else:  # Neutral
        # Straight eyebrows
        cv2.line(img, (14, 14), (20, 14), 30, 1)
        cv2.line(img, (28, 14), (34, 14), 30, 1)
        # Neutral horizontal mouth
        cv2.line(img, (18, 33), (30, 33), 30, 1)

    # Add realistic texture noise
    noise = np.random.normal(0, 8, (48, 48)).astype(np.int16)
    noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy_img


class FacialExpressionDataset(Dataset):
    def __init__(self, images: np.ndarray, labels: np.ndarray):
        # images shape: (N, 48, 48), normalize to [0, 1] and add channel dimension (N, 1, 48, 48)
        self.images = torch.tensor(images, dtype=torch.float32).unsqueeze(1) / 255.0
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]


def create_expression_dataloaders(samples_per_class: int = 120, batch_size: int = 32, seed: int = 42):
    np.random.seed(seed)
    images = []
    labels = []

    for label_idx, expr in enumerate(EXPRESSION_CLASSES):
        for s in range(samples_per_class):
            img = synthesize_face_image(expr, seed=seed * 1000 + label_idx * 500 + s)
            images.append(img)
            labels.append(label_idx)

    images = np.array(images)
    labels = np.array(labels)

    indices = np.random.permutation(len(labels))
    images = images[indices]
    labels = labels[indices]

    split_idx = int(0.8 * len(labels))
    train_imgs, test_imgs = images[:split_idx], images[split_idx:]
    train_lbls, test_lbls = labels[:split_idx], labels[split_idx:]

    train_ds = FacialExpressionDataset(train_imgs, train_lbls)
    test_ds = FacialExpressionDataset(test_imgs, test_lbls)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader, test_imgs, test_lbls
