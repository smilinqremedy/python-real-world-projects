# Project 92: Real-Time Object Detection System

## Overview

The **Real-Time Object Detection System** is a computer vision application built using Python, YOLO architecture principles, Non-Maximum Suppression (NMS), and standard COCO categories.

The system allows users to:
1. Detect multiple objects across 80 COCO categories simultaneously.
2. Localize objects with precise spatial bounding boxes `(x_min, y_min, x_max, y_max)`.
3. Filter detections by confidence threshold and suppress duplicates using IoU-based Non-Maximum Suppression.
4. Count and aggregate detected objects by category.
5. Process still images, recorded video streams, and live webcam feeds.
6. Export detection outputs into annotated images, structured JSON, and CSV reports.

---

## Technical Foundations

### Object Detection vs. Image Classification
- **Image Classification:** Categorizes the image as a single whole (e.g. *A photo of a street*). It does not provide information about object counts, distinct instances, or their coordinates.
- **Object Detection:** Identifies *what* items are present, *how many* exist, and *where* each item is spatially located within bounding box coordinates.

### Non-Maximum Suppression (NMS) & Intersection-over-Union (IoU)
1. **Intersection-over-Union (IoU):**
   $$\\text{IoU} = \\frac{\\text{Area of Overlap}(A, B)}{\\text{Area of Union}(A, B)}$$
2. **NMS Algorithm:** Sorts all bounding boxes by descending confidence. Selects the most confident candidate and suppresses any subsequent boxes sharing the same class whose IoU exceeds the suppression threshold (e.g. 0.45).

---

## Architecture

```text
92-real-time-object-detection/
├── app.py                   # Streamlit interactive dashboard
├── detector.py              # Detection dataclass, IoU, NMS, and detection engine
├── main.py                  # CLI command runner
├── media_processor.py       # Image, video, and webcam ingestion & export
├── requirements.txt         # Dependencies
├── test_object_detection.py # Automated unit test suite
├── visualizer.py            # Bounding box rendering & category aggregation
└── README.md                # Documentation
```

---

## Installation & Setup

1. Navigate to the project folder:
   ```bash
   cd 92-real-time-object-detection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Detect Objects in an Image via CLI
```bash
python3 main.py --image path/to/image.jpg --conf 0.35 --iou 0.45 --save output_result
```
Outputs:
- `output_result_annotated.png`
- `output_result_detections.json`
- `output_result_report.csv`

### 2. Video File Processing
```bash
python3 main.py --video path/to/video.mp4 --conf 0.40
```

### 3. Webcam Live Feed (where hardware camera is present)
```bash
python3 main.py --webcam
```

### 4. Interactive Streamlit Interface
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_object_detection.py -v
```
