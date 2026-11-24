"""
Visualization and Diagnostic Plotting for Wearable Sensor Signals.
Renders waveform activity profiles and ASCII confusion matrix summaries.
"""
from typing import Dict, Any, List
import numpy as np
from PIL import Image, ImageDraw
from dataset import ACTIVITIES, CHANNELS


def render_sensor_waveform_image(
    sensor_window: np.ndarray,
    width: int = 500,
    height: int = 240
) -> Image.Image:
    """
    Renders 6-channel sensor time-series waveforms (3 acc, 3 gyro) onto a canvas image.
    sensor_window: shape (6, window_size)
    """
    canvas = Image.new("RGB", (width, height), color=(20, 24, 32))
    draw = ImageDraw.Draw(canvas)

    num_channels, win_len = sensor_window.shape
    colors = ["#FF4444", "#44FF44", "#4488FF", "#FFAA00", "#FF44FF", "#00FFFF"]

    # Draw zero reference line
    mid_y = height // 2
    draw.line([(40, mid_y), (width - 10, mid_y)], fill="#444455", width=1)

    # Plot each channel
    x_coords = np.linspace(40, width - 10, win_len)
    for c_idx in range(num_channels):
        raw = sensor_window[c_idx]
        # Scale amplitude to pixel range
        scaled_y = mid_y - (raw * 40.0)
        pts = [(int(x_coords[i]), int(np.clip(scaled_y[i], 10, height - 10))) for i in range(win_len)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=colors[c_idx % len(colors)], width=2)

    # Legend text
    draw.text((10, 10), "Acc (X:Red, Y:Grn, Z:Blu) | Gyro (X:Org, Y:Pur, Z:Cyn)", fill="#FFFFFF")
    return canvas


def format_confusion_matrix_ascii(cm: List[List[int]]) -> str:
    """Formats an NxN confusion matrix into a clean ASCII table."""
    lines = []
    header = "Actual \\ Pred | " + " | ".join(f"{a[:4]:>4}" for a in ACTIVITIES)
    lines.append(header)
    lines.append("-" * len(header))
    for i, row in enumerate(cm):
        row_str = f"{ACTIVITIES[i][:11]:<13} | " + " | ".join(f"{val:>4}" for val in row)
        lines.append(row_str)
    return "\n".join(lines)
