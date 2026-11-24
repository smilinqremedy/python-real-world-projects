"""
Automated unit tests for Real-Time Object Detection System.
"""
import unittest
import os
import shutil
import tempfile
import json
from PIL import Image, ImageDraw

from detector import (
    Detection,
    compute_iou,
    apply_nms,
    ObjectDetector,
    COCO_CLASSES
)
from visualizer import draw_bounding_boxes, count_detections_by_category
from media_processor import MediaProcessor, MediaProcessingError


class TestRealTimeObjectDetection(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_img_path = os.path.join(self.test_dir, "test_input.png")

        # Create a test image with high-contrast distinct shapes
        img = Image.new("RGB", (200, 200), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        # Person-like vertical rectangle
        draw.rectangle([20, 20, 60, 150], fill=(20, 40, 180))
        # Car-like horizontal rectangle
        draw.rectangle([80, 80, 180, 140], fill=(200, 30, 30))
        img.save(self.test_img_path, "PNG")

        self.detector = ObjectDetector()
        self.processor = MediaProcessor(detector=self.detector)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_iou_computation(self):
        # Identical boxes: IoU must be 1.0
        box1 = (0, 0, 10, 10)
        box2 = (0, 0, 10, 10)
        self.assertAlmostEqual(compute_iou(box1, box2), 1.0, places=4)

        # Completely disjoint boxes: IoU must be 0.0
        box3 = (20, 20, 30, 30)
        self.assertAlmostEqual(compute_iou(box1, box3), 0.0, places=4)

        # Partial overlap
        # boxA: (0, 0, 10, 10), area = 100
        # boxB: (5, 0, 15, 10), area = 100
        # Inter: (5, 0, 10, 10), area = 50
        # Union: 100 + 100 - 50 = 150
        # IoU = 50 / 150 = 1/3
        boxA = (0, 0, 10, 10)
        boxB = (5, 0, 15, 10)
        self.assertAlmostEqual(compute_iou(boxA, boxB), 50.0 / 150.0, places=4)

    def test_nms_suppression(self):
        det1 = Detection(x_min=10, y_min=10, x_max=50, y_max=50, confidence=0.9, class_id=0, class_name="person")
        # Strongly overlapping candidate with lower confidence
        det2 = Detection(x_min=12, y_min=12, x_max=50, y_max=50, confidence=0.7, class_id=0, class_name="person")
        # Different class overlapping candidate: should NOT be suppressed
        det3 = Detection(x_min=12, y_min=12, x_max=50, y_max=50, confidence=0.85, class_id=2, class_name="car")

        dets = [det1, det2, det3]
        kept = apply_nms(dets, iou_threshold=0.5)

        # det2 should be suppressed, leaving det1 and det3
        self.assertEqual(len(kept), 2)
        kept_names = {d.class_name for d in kept}
        self.assertIn("person", kept_names)
        self.assertIn("car", kept_names)
        self.assertEqual(max(d.confidence for d in kept if d.class_name == "person"), 0.9)

    def test_detection_and_category_counting(self):
        with Image.open(self.test_img_path) as img:
            dets = self.detector.detect(img, conf_threshold=0.2)
            self.assertTrue(len(dets) > 0)
            for d in dets:
                self.assertIn(d.class_name, COCO_CLASSES)
                self.assertGreaterEqual(d.confidence, 0.2)
                self.assertGreater(d.x_max, d.x_min)
                self.assertGreater(d.y_max, d.y_min)

            counts = count_detections_by_category(dets)
            self.assertEqual(sum(counts.values()), len(dets))

    def test_visualizer_rendering(self):
        with Image.open(self.test_img_path) as img:
            dets = [
                Detection(x_min=10, y_min=10, x_max=60, y_max=120, confidence=0.88, class_id=0, class_name="person"),
                Detection(x_min=80, y_min=80, x_max=160, y_max=130, confidence=0.75, class_id=2, class_name="car")
            ]
            annotated = draw_bounding_boxes(img, dets)
            self.assertEqual(annotated.size, img.size)

    def test_media_processor_image_and_saving(self):
        out_prefix = os.path.join(self.test_dir, "output_test")
        res = self.processor.process_image(self.test_img_path, conf_threshold=0.2)

        self.assertIn("total_detections", res)
        self.assertIn("category_counts", res)
        self.assertIn("annotated_image", res)

        saved = self.processor.save_results(res, out_prefix)
        self.assertIn("image", saved)
        self.assertIn("json", saved)
        self.assertIn("csv", saved)

        self.assertTrue(os.path.exists(saved["image"]))
        self.assertTrue(os.path.exists(saved["json"]))
        self.assertTrue(os.path.exists(saved["csv"]))

        # Verify JSON content
        with open(saved["json"], "r") as f:
            data = json.load(f)
            self.assertIn("total_detections", data)
            self.assertIn("category_counts", data)

    def test_invalid_and_corrupt_files(self):
        # Missing file
        with self.assertRaises(MediaProcessingError):
            self.processor.process_image("missing_file.jpg")

        # Unsupported extension
        unsupported = os.path.join(self.test_dir, "doc.txt")
        with open(unsupported, "w") as f:
            f.write("hello")
        with self.assertRaises(MediaProcessingError):
            self.processor.process_image(unsupported)

        # Empty image file
        empty_img = os.path.join(self.test_dir, "empty.jpg")
        with open(empty_img, "wb") as f:
            f.write(b"")
        with self.assertRaises(MediaProcessingError):
            self.processor.process_image(empty_img)

    def test_camera_availability_handling(self):
        ok, msg = self.processor.check_camera_availability(999)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)
        # Should handle gracefully without raising unhandled exception


if __name__ == "__main__":
    unittest.main()
