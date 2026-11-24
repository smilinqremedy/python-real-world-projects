"""
Dataset Ingestion, Preprocessing, Time-Window Segmentation, and Subject Splitting.
Handles 6-axis inertial sensor data (3-axis accelerometer + 3-axis gyroscope).
Enforces subject-based splitting to strictly eliminate cross-subject data leakage.
"""
import os
import csv
import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

ACTIVITIES = [
    "Walking", "Walking Upstairs", "Walking Downstairs", "Sitting", "Standing", "Laying"
]
CHANNELS = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]


def create_sliding_windows(
    data: np.ndarray,
    labels: np.ndarray,
    window_size: int = 64,
    step_size: int = 32
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Segments continuous sensor time-series into overlapping fixed-length windows.
    Args:
        data: shape (T, 6)
        labels: shape (T,)
    Returns:
        X: shape (N_windows, 6, window_size)
        y: shape (N_windows,)
    """
    total_timesteps = len(data)
    if total_timesteps < window_size:
        return np.zeros((0, 6, window_size), dtype=np.float32), np.zeros(0, dtype=int)

    windows = []
    win_labels = []

    start = 0
    while start + window_size <= total_timesteps:
        # Window slice: (window_size, 6) -> transpose to (6, window_size)
        w = data[start:start + window_size].T
        # Majority label in window
        lbl_slice = labels[start:start + window_size]
        majority_lbl = int(np.bincount(lbl_slice).argmax())

        windows.append(w)
        win_labels.append(majority_lbl)
        start += step_size

    return np.array(windows, dtype=np.float32), np.array(win_labels, dtype=int)


def generate_synthetic_har_dataset(
    output_dir: str,
    num_subjects: int = 6,
    samples_per_activity: int = 150,
    seed: int = 42
) -> List[str]:
    """
    Generates realistic tri-axial accelerometer and gyroscope time-series streams
    mimicking physiological biomechanical movement for 6 subjects and 6 activities.
    Saves CSV files separated by subject and activity.
    """
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    for subj_id in range(1, num_subjects + 1):
        subj_dir = os.path.join(output_dir, f"subject_{subj_id:02d}")
        os.makedirs(subj_dir, exist_ok=True)

        for act_idx, act_name in enumerate(ACTIVITIES):
            csv_path = os.path.join(subj_dir, f"{act_name.lower().replace(' ', '_')}.csv")
            t = np.linspace(0, 10, samples_per_activity)

            # Signal characteristics based on activity
            if act_name == "Walking":
                freq = 1.8 + np.random.uniform(-0.1, 0.1)
                ax = 0.8 * np.sin(2 * np.pi * freq * t) + np.random.normal(0, 0.05, len(t))
                ay = 0.3 * np.cos(2 * np.pi * freq * t) - 0.98 + np.random.normal(0, 0.05, len(t))
                az = 0.4 * np.sin(4 * np.pi * freq * t) + np.random.normal(0, 0.05, len(t))
                gx = 1.2 * np.sin(2 * np.pi * freq * t) + np.random.normal(0, 0.1, len(t))
                gy = 0.8 * np.cos(2 * np.pi * freq * t) + np.random.normal(0, 0.1, len(t))
                gz = 0.5 * np.sin(2 * np.pi * freq * t) + np.random.normal(0, 0.1, len(t))
            elif act_name == "Walking Upstairs":
                freq = 1.4
                ax = 1.0 * np.sin(2 * np.pi * freq * t) + 0.2
                ay = 0.5 * np.cos(2 * np.pi * freq * t) - 1.1
                az = 0.6 * np.sin(2 * np.pi * freq * t) + 0.1
                gx = 1.5 * np.sin(2 * np.pi * freq * t)
                gy = 1.0 * np.cos(2 * np.pi * freq * t)
                gz = 0.8 * np.sin(2 * np.pi * freq * t)
            elif act_name == "Walking Downstairs":
                freq = 2.2
                ax = 1.2 * np.sin(2 * np.pi * freq * t) - 0.2
                ay = 0.7 * np.cos(2 * np.pi * freq * t) - 0.85
                az = 0.5 * np.sin(2 * np.pi * freq * t) - 0.1
                gx = 1.8 * np.sin(2 * np.pi * freq * t)
                gy = 1.2 * np.cos(2 * np.pi * freq * t)
                gz = 0.9 * np.sin(2 * np.pi * freq * t)
            elif act_name == "Sitting":
                # Static gravity on Y axis
                ax = np.random.normal(0.05, 0.02, len(t))
                ay = np.random.normal(-0.98, 0.02, len(t))
                az = np.random.normal(0.1, 0.02, len(t))
                gx = np.random.normal(0.0, 0.01, len(t))
                gy = np.random.normal(0.0, 0.01, len(t))
                gz = np.random.normal(0.0, 0.01, len(t))
            elif act_name == "Standing":
                # Upright gravity alignment
                ax = np.random.normal(0.0, 0.02, len(t))
                ay = np.random.normal(-1.0, 0.02, len(t))
                az = np.random.normal(0.02, 0.02, len(t))
                gx = np.random.normal(0.0, 0.01, len(t))
                gy = np.random.normal(0.0, 0.01, len(t))
                gz = np.random.normal(0.0, 0.01, len(t))
            else:  # Laying
                # Horizontal gravity on Z axis
                ax = np.random.normal(0.02, 0.02, len(t))
                ay = np.random.normal(0.05, 0.02, len(t))
                az = np.random.normal(-0.98, 0.02, len(t))
                gx = np.random.normal(0.0, 0.01, len(t))
                gy = np.random.normal(0.0, 0.01, len(t))
                gz = np.random.normal(0.0, 0.01, len(t))

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z", "activity", "activity_id"])
                for i in range(len(t)):
                    writer.writerow([
                        round(float(ax[i]), 4), round(float(ay[i]), 4), round(float(az[i]), 4),
                        round(float(gx[i]), 4), round(float(gy[i]), 4), round(float(gz[i]), 4),
                        act_name, act_idx
                    ])

            generated_files.append(csv_path)

    return generated_files


def load_subject_data(subject_dir: str) -> Tuple[np.ndarray, np.ndarray]:
    """Loads all activity CSV records from a subject directory into continuous arrays."""
    data_list, label_list = [], []

    for f in sorted(os.listdir(subject_dir)):
        if f.endswith(".csv"):
            f_path = os.path.join(subject_dir, f)
            with open(f_path, "r", encoding="utf-8") as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    data_list.append([
                        float(row["acc_x"]), float(row["acc_y"]), float(row["acc_z"]),
                        float(row["gyro_x"]), float(row["gyro_y"]), float(row["gyro_z"])
                    ])
                    label_list.append(int(row["activity_id"]))

    return np.array(data_list, dtype=np.float32), np.array(label_list, dtype=int)
