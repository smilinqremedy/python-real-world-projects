"""
Streamlit Web Interface for AI-Based Medical Image Classification.
Allows clinicians/researchers to upload X-rays, view class probabilities,
review safety disclaimers, and inspect past screening audit logs.
"""
import os
import tempfile
import streamlit as st
from PIL import Image
from classifier import MedicalClassifierService, CLINICAL_SAFETY_DISCLAIMER
from dataset import CLASSES
import database

st.set_page_config(
    page_title="Medical Image Classifier",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 AI-Based Medical Image Classification System")
st.markdown("### Chest Radiography Screening & Pulmonary Opacity Detection")

# Prominent Medical Disclaimer Banner
st.warning(f"⚠️ **REGULATORY & CLINICAL ADVISORY:**\n\n{CLINICAL_SAFETY_DISCLAIMER}")

service = MedicalClassifierService()

tabs = st.tabs(["🔍 Image Screening", "📊 Screening History", "ℹ️ About & Ethics"])

with tabs[0]:
    st.subheader("Upload Radiographic Image (Chest X-Ray)")
    uploaded_file = st.file_uploader("Select PNG or JPEG X-ray", type=["png", "jpg", "jpeg"])

    notes = st.text_input("Clinical / Study Notes (Optional):")

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])

        with col1:
            img = Image.open(uploaded_file)
            st.image(img, caption=f"Uploaded Image: {uploaded_file.name}", use_column_width=True)

        with col2:
            st.write("#### Classification Analysis")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                res = service.classify_image(tmp_path, user_notes=notes)
                if res["success"]:
                    pred_class = res["predicted_class"]
                    conf = res["confidence_score"] * 100

                    if pred_class == "Normal":
                        st.success(f"**Predicted Screening:** {pred_class} ({conf:.1f}% confidence)")
                    else:
                        st.error(f"**Predicted Screening:** {pred_class} ({conf:.1f}% confidence)")

                    st.write("**Class Probability Distribution:**")
                    for cls_name, prob in res["probabilities"].items():
                        st.write(f"- **{cls_name}**: `{prob * 100:.1f}%`")
                        st.progress(prob)

                    st.info(f"Audit Log ID: `{res['log_id']}` (Recorded to local SQLite database)")
                else:
                    st.error(res["error"])
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

with tabs[1]:
    st.subheader("Historical Screening Audit Log")
    history = database.get_prediction_history(limit=25)
    if history:
        st.dataframe(history)
    else:
        st.write("No screening records found in database yet.")

with tabs[2]:
    st.subheader("System Architecture & Clinical Limitations")
    st.markdown("""
    - **Model Architecture:** Custom Convolutional Neural Network (CNN) with multi-stage feature extraction, spatial pooling, and dense decision head.
    - **Preprocess Pipeline:** Resizing to 64x64, zero-mean grayscale standardization, channel normalization.
    - **Limitation:** Model trained on radiographic features. Performance may vary significantly based on patient position, scanner calibration, and comorbidities.
    """)
