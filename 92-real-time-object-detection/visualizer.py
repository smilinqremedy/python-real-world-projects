"""
Visualization module for rendering bounding boxes, labels, confidence scores,
and category frequency summary tables.
"""
from typing import List, Dict, Any, Tuple
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
from detector import Detection

# Color palette mapped by class index modulo length
BOX_COLORS = [
    "#FF3838", "#FF9D97", "#FF701F", "#FFB21D", "#CFD231",
    "#48F90A", "#92CC17", "#3DDB86", "#1A9334", "#00D4BB",
    "#2C99A8", "#00A2FF", "#3878FF", "#855BF2", "#9E41E6"
]


def count_detections_by_category(detections: List[Detection]) -> Dict[str, int]:
    """Returns a dictionary mapping class_name -> total occurrence count."""
    counter = Counter(d.class_name for d in detections)
    return dict(counter)


def draw_bounding_boxes(
    image: Image.Image,
    detections: List[Detection],
    box_width: int = 3,
    font_size: int = 14
) -> Image.Image:
    """
    Renders bounding boxes with labels and confidence percentages onto a copy of the image.
    """
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for det in detections:
        color = BOX_COLORS[det.class_id % len(BOX_COLORS)]
        # Draw bounding rectangle
        draw.rectangle(
            [det.x_min, det.y_min, det.x_max, det.y_max],
            outline=color,
            width=box_width
        )

        # Label tag text
        label_text = f"{det.class_name} {det.confidence * 100:.1f}%"

        # Background tag rectangle
        tag_height = font_size + 4
        tag_width = len(label_text) * 7 + 8
        tag_y1 = max(0, det.y_min - tag_height)
        tag_y2 = det.y_min
        tag_x1 = det.x_min
        tag_x2 = det.x_min + tag_width

        draw.rectangle([tag_x1, tag_y1, tag_x2, tag_y2], fill=color)
        draw.text((tag_x1 + 4, tag_y1 + 2), label_text, fill="#FFFFFF", font=font)

    return canvas
