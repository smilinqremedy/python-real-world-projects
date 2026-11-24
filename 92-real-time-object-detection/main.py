"""
Command-Line Interface for Real-Time Object Detection System.
"""
import argparse
import sys
import os
import json
from detector import ObjectDetector
from media_processor import MediaProcessor, MediaProcessingError


def main():
    parser = argparse.ArgumentParser(description="Real-Time Object Detection System (YOLO / COCO)")
    parser.add_argument("--image", type=str, help="Path to input image for object detection")
    parser.add_argument("--video", type=str, help="Path to input video file")
    parser.add_argument("--webcam", action="store_true", help="Launch live webcam detection feed")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold (0.0 to 1.0)")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold (0.0 to 1.0)")
    parser.add_argument("--save", type=str, default="output", help="Output prefix path for saved artifacts")
    parser.add_argument("--weights", type=str, default=None, help="Optional path to custom YOLO weights (.pt)")

    args = parser.parse_args()
    detector = ObjectDetector(weights_path=args.weights)
    processor = MediaProcessor(detector=detector)

    if args.webcam:
        print("Checking webcam availability...")
        ok, msg = processor.check_camera_availability(0)
        print(f"Status: {msg}")
        if not ok:
            print("Notice: Physical webcam not available on this host. Use --image or --video instead.")
            sys.exit(0)

        import cv2
        cap = cv2.VideoCapture(0)
        print("Starting webcam stream. Press 'q' to exit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Process frame
            from PIL import Image
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            dets = detector.detect(pil_img, conf_threshold=args.conf, iou_threshold=args.iou)
            for d in dets:
                cv2.rectangle(frame, (d.x_min, d.y_min), (d.x_max, d.y_max), (0, 255, 0), 2)
                cv2.putText(frame, f"{d.class_name} {d.confidence:.2f}", (d.x_min, d.y_min - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imshow("Real-Time Object Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        return

    if args.image:
        print(f"Processing image: {args.image}")
        try:
            res = processor.process_image(args.image, conf_threshold=args.conf, iou_threshold=args.iou)
            print(f"Total Detections: {res['total_detections']}")
            print("Category Counts:")
            for cat, count in res["category_counts"].items():
                print(f"  - {cat}: {count}")

            saved = processor.save_results(res, args.save)
            print(f"Saved artifacts:")
            for k, p in saved.items():
                print(f"  - {k}: {p}")
        except MediaProcessingError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.video:
        print(f"Processing video: {args.video}")
        try:
            res = processor.process_video_frames(args.video, conf_threshold=args.conf)
            print(f"Processed {res['total_frames_processed']} frames.")
            print(f"Cumulative Category Counts: {json.dumps(res['cumulative_category_counts'], indent=2)}")
        except MediaProcessingError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
