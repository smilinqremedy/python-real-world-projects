"""
Streamlit Web Interface for Real-Time Object Detection System.
Supports image uploads, video files, webcam diagnostics, and result exports.
"""
import io
import os
import tempfile
import json
import streamlit as st
from PIL import Image

from detector import ObjectDetector, compute_iou
from visualizer import draw_bounding_boxes, count_detections_by_category
from media_processor import MediaProcessor, MediaProcessingError

st.set_page_config(
    page_title="Real-Time Object Detection",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Real-Time Object Detection System")
st.markdown("Computer Vision detection powered by YOLO architecture, COCO categories, and Non-Maximum Suppression.")

# Sidebar Settings
st.sidebar.header("Detection Parameters")
conf_threshold = st.sidebar.slider("Confidence Threshold", min_value=0.1, max_value=0.95, value=0.35, step=0.05)
iou_threshold = st.sidebar.slider("NMS IoU Threshold", min_value=0.1, max_value=0.9, value=0.45, step=0.05)
st.sidebar.markdown("---")
st.sidebar.info("Boxes below confidence threshold are discarded; overlapping candidate boxes are suppressed using NMS.")

processor = MediaProcessor()

tabs = st.tabs(["🖼️ Image Detection", "🎥 Video Detection", "📹 Webcam Stream", "📘 Technical Guide"])

with tabs[0]:
    st.subheader("Upload Static Image")
    uploaded_image = st.file_uploader("Select PNG, JPG, or BMP", type=["png", "jpg", "jpeg", "bmp"])

    if uploaded_image is not None:
        try:
            image = Image.open(uploaded_image).convert("RGB")
            col1, col2 = st.columns([1, 1])

            with col1:
                st.image(image, caption="Original Input Image", use_column_width=True)

            # Perform detection
            detections = processor.detector.detect(image, conf_threshold=conf_threshold, iou_threshold=iou_threshold)
            annotated = draw_bounding_boxes(image, detections)
            counts = count_detections_by_category(detections)

            with col2:
                st.image(annotated, caption=f"Detection Output ({len(detections)} objects found)", use_column_width=True)

            st.write("### Detection Breakdown & Counts")
            if counts:
                cols = st.columns(len(counts))
                for idx, (cat, count) in enumerate(counts.items()):
                    cols[idx % len(cols)].metric(label=cat.capitalize(), value=count)

                # Export downloads
                st.write("### Export Detection Artifacts")
                col_d1, col_d2 = st.columns(2)

                buf = io.BytesIO()
                annotated.save(buf, format="PNG")
                col_d1.download_button(
                    label="💾 Download Annotated Image",
                    data=buf.getvalue(),
                    file_name="detected_objects.png",
                    mime="image/png"
                )

                json_str = json.dumps([d.to_dict() for d in detections], indent=2)
                col_d2.download_button(
                    label="📄 Download Detection JSON",
                    data=json_str,
                    file_name="detections.json",
                    mime="application/json"
                )
            else:
                st.info("No objects detected above the chosen confidence threshold. Try lowering the threshold in the sidebar.")

        except Exception as e:
            st.error(f"Error processing image: {e}")

with tabs[1]:
    st.subheader("Upload Recorded Video")
    uploaded_video = st.file_uploader("Select MP4, AVI, or MOV", type=["mp4", "avi", "mov"])
    if uploaded_video is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_video.getvalue())
            tmp_path = tmp.name

        try:
            st.info("Processing video frames...")
            res = processor.process_video_frames(tmp_path, conf_threshold=conf_threshold, max_frames=20)
            st.success(f"Processed {res['total_frames_processed']} frames successfully!")
            st.write("#### Cumulative Detected Categories:")
            st.json(res["cumulative_category_counts"])
        except MediaProcessingError as mpe:
            st.warning(f"Video Notice: {mpe}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

with tabs[2]:
    st.subheader("Webcam Diagnostic & Real-Time Feed")
    cam_available, cam_msg = processor.check_camera_availability(camera_index=0)
    if cam_available:
        st.success(f"✅ {cam_msg}")
        st.write("Live webcam capture is supported. Use the CLI `python3 main.py --webcam` for streaming visual HUD.")
    else:
        st.warning(f"⚠️ Camera Status: {cam_msg}")
        st.caption("On headless virtual environments or cloud containers, physical hardware cameras are absent by design.")

with tabs[3]:
    st.subheader("Core Technical Concepts")
    st.markdown("""
    ### Object Detection vs. Image Classification
    - **Image Classification:** Assigns a single categorical label to an entire image (e.g. *This image contains a dog*). It answers *what* is in the image, but not *where*.
    - **Object Detection:** Identifies multiple objects, determines their specific classes, and predicts precise spatial coordinates enclosing each instance via **bounding boxes** `(x_min, y_min, x_max, y_max)`. It answers *what* is in the image and *where* each object is located.

    ### Bounding Box Generation & Non-Maximum Suppression (NMS)
    1. **Anchor Boxes:** The network predicts candidate boxes across multi-scale feature maps.
    2. **Confidence Filtering:** Candidates with confidence scores below the threshold are discarded.
    3. **Intersection-over-Union (IoU):** Quantifies spatial overlap between candidate boxes:
       $$\\text{IoU} = \\frac{\\text{Area of Overlap}}{\\text{Area of Union}}$$
    4. **Non-Maximum Suppression:** For each category, the box with the highest confidence is selected, and all neighboring overlapping boxes with an $\\text{IoU} > \\text{threshold}$ are suppressed to prevent duplicate detections.
    """)
