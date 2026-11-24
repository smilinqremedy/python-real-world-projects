"""
Media processing pipeline handling images, videos, and camera streams.
Includes input validation, unsupported format error handling, and result export.
"""
import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from detector import Detection, ObjectDetector
from visualizer import draw_bounding_boxes, count_detections_by_category

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
SUPPORTED_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


class MediaProcessingError(Exception):
    """Raised when media input is invalid, corrupted, or unsupported."""
    pass


class MediaProcessor:
    def __init__(self, detector: Optional[ObjectDetector] = None):
        self.detector = detector or ObjectDetector()

    def validate_file(self, file_path: str, allowed_extensions: set) -> None:
        """Validates existence, non-empty size, and allowed extensions."""
        if not os.path.exists(file_path):
            raise MediaProcessingError(f"File not found: {file_path}")
        if os.path.getsize(file_path) == 0:
            raise MediaProcessingError(f"File is empty (0 bytes): {file_path}")
        _, ext = os.path.splitext(file_path.lower())
        if ext not in allowed_extensions:
            raise MediaProcessingError(
                f"Unsupported format '{ext}'. Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            )

    def process_image(
        self,
        image_path: str,
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.45
    ) -> Dict[str, Any]:
        """
        Loads, validates, and runs object detection on an image.
        Returns detections, category counts, and annotated image.
        """
        self.validate_file(image_path, SUPPORTED_IMAGE_EXTS)
        try:
            with Image.open(image_path) as img:
                img_rgb = img.convert("RGB")
        except Exception as e:
            raise MediaProcessingError(f"Corrupted or unreadable image file: {e}")

        detections = self.detector.detect(img_rgb, conf_threshold, iou_threshold)
        counts = count_detections_by_category(detections)
        annotated_image = draw_bounding_boxes(img_rgb, detections)

        return {
            "image_path": image_path,
            "width": img_rgb.width,
            "height": img_rgb.height,
            "total_detections": len(detections),
            "category_counts": counts,
            "detections": [d.to_dict() for d in detections],
            "annotated_image": annotated_image
        }

    def process_video_frames(
        self,
        video_path: str,
        conf_threshold: float = 0.35,
        max_frames: int = 30
    ) -> Dict[str, Any]:
        """
        Extracts and detects objects in video frames.
        Gracefully handles missing cv2 or corrupted video.
        """
        self.validate_file(video_path, SUPPORTED_VIDEO_EXTS)

        try:
            import cv2
        except ImportError:
            raise MediaProcessingError(
                "OpenCV (cv2) is required for video decoding. Install opencv-python or opencv-python-headless."
            )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise MediaProcessingError(f"Unable to open video stream: {video_path}")

        frame_count = 0
        all_counts: Dict[str, int] = {}
        processed_frames_summary = []

        try:
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                # Convert BGR to RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                dets = self.detector.detect(pil_img, conf_threshold=conf_threshold)
                c = count_detections_by_category(dets)
                for k, v in c.items():
                    all_counts[k] = all_counts.get(k, 0) + v

                processed_frames_summary.append({
                    "frame_number": frame_count,
                    "detections_count": len(dets)
                })
        finally:
            cap.release()

        return {
            "video_path": video_path,
            "total_frames_processed": frame_count,
            "cumulative_category_counts": all_counts,
            "frames": processed_frames_summary
        }

    def check_camera_availability(self, camera_index: int = 0) -> Tuple[bool, str]:
        """Checks if a webcam device is accessible without crashing."""
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                cap.release()
                return False, f"Webcam index {camera_index} is unavailable or access is denied."
            ret, _ = cap.read()
            cap.release()
            if not ret:
                return False, f"Webcam index {camera_index} connected but failed to capture frame."
            return True, "Webcam is active and operational."
        except ImportError:
            return False, "OpenCV (cv2) library is not installed."
        except Exception as e:
            return False, f"Camera error: {str(e)}"

    def save_results(self, result: Dict[str, Any], output_prefix: str) -> Dict[str, str]:
        """Saves annotated image, JSON metadata, and CSV detection logs."""
        os.makedirs(os.path.dirname(os.path.abspath(output_prefix)), exist_ok=True)
        saved_files = {}

        # Save annotated image
        if "annotated_image" in result and result["annotated_image"] is not None:
            img_out = f"{output_prefix}_annotated.png"
            result["annotated_image"].save(img_out)
            saved_files["image"] = img_out

        # Save JSON metadata
        json_out = f"{output_prefix}_detections.json"
        meta = {
            "total_detections": result.get("total_detections", 0),
            "category_counts": result.get("category_counts", {}),
            "detections": result.get("detections", [])
        }
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        saved_files["json"] = json_out

        # Save CSV report
        csv_out = f"{output_prefix}_report.csv"
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Class Name", "Confidence", "x_min", "y_min", "x_max", "y_max"])
            for d in result.get("detections", []):
                writer.writerow([d["class_name"], d["confidence"], d["x_min"], d["y_min"], d["x_max"], d["y_max"]])
        saved_files["csv"] = csv_out

        return saved_files
