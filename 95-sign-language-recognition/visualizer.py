"""
Visualizer module for rendering hand skeletal graphs, joint landmarks,
and real-time Heads-Up Display (HUD) sign predictions.
"""
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from hand_detector import HAND_CONNECTIONS


def render_hand_skeleton_hud(
    image: Image.Image,
    landmarks_21: np.ndarray,
    predicted_sign: str,
    confidence: float
) -> Image.Image:
    """
    Renders 21 skeletal joints, connecting bone segments, and predicted sign HUD on image canvas.
    landmarks_21: (21, 3) coordinates.
    """
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    W, H = canvas.size

    # Convert coordinates to image pixel space
    # Assuming coordinates centered at middle of canvas if normalized
    pts = []
    for i in range(21):
        x = int(W * 0.5 + landmarks_21[i, 0] * W * 0.35)
        y = int(H * 0.7 - landmarks_21[i, 1] * H * 0.35)
        pts.append((x, y))

    # Draw skeletal bones
    for joint_a, joint_b in HAND_CONNECTIONS:
        if joint_a < len(pts) and joint_b < len(pts):
            draw.line([pts[joint_a], pts[joint_b]], fill="#00FFCC", width=3)

    # Draw joint nodes
    for idx, (x, y) in enumerate(pts):
        r = 5 if idx in [4, 8, 12, 16, 20] else 3  # Larger circles for fingertips
        node_color = "#FF0055" if idx in [4, 8, 12, 16, 20] else "#FFFF00"
        draw.ellipse([x - r, y - r, x + r, y + r], fill=node_color, outline="#000000")

    # Render HUD overlay banner at top
    hud_h = 50
    draw.rectangle([10, 10, W - 10, 10 + hud_h], fill="#111122", outline="#00FFCC", width=2)
    label_text = f"Sign: {predicted_sign.upper()}  |  Conf: {confidence * 100:.1f}%"
    draw.text((25, 25), label_text, fill="#FFFFFF")

    return canvas
