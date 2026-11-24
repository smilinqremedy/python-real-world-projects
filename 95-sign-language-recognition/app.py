"""
Streamlit Web Interface for AI-Powered Sign Language Recognition System.
Interactive gesture classification, 21-point skeleton rendering, and sign dictionary guide.
"""
import streamlit as st
import numpy as np
from PIL import Image

from sign_dictionary import SIGN_DICTIONARY, SUPPORTED_SIGNS, ETHICAL_LINGUISTIC_DISCLAIMER
from hand_detector import (
    get_canonical_sign_landmarks,
    normalize_landmarks,
    generate_landmark_dataset
)
from classifier import SignClassifier
from visualizer import render_hand_skeleton_hud
from evaluator import SignEvaluator

st.set_page_config(
    page_title="Sign Language Recognition",
    page_icon="🤟",
    layout="wide"
)

st.title("🤟 AI-Powered Sign Language Recognition System")
st.markdown("Computer Vision hand landmark extraction (21 3D keypoints) and gesture classification.")

# Prominent Linguistic Advisory
st.warning(f"⚠️ **ETHICAL & LINGUISTIC ADVISORY:**\n\n{ETHICAL_LINGUISTIC_DISCLAIMER}")

# Cache classifier instance
@st.cache_resource
def get_trained_classifier():
    clf = SignClassifier()
    X, y = generate_landmark_dataset(samples_per_sign=25, seed=42)
    clf.train(X, y, epochs=12, lr=0.05)
    return clf

classifier = get_trained_classifier()

tabs = st.tabs([
    "🎯 Gesture Recognition",
    "📖 Sign Dictionary & Guidelines",
    "📊 Model Training & Evaluation",
    "🌐 Regional Variations & Ethics"
])

with tabs[0]:
    st.subheader("Test Sign Recognition")
    col1, col2 = st.columns([1, 1])

    with col1:
        selected_sign = st.selectbox("Select Benchmark Sign Posture to Simulate:", SUPPORTED_SIGNS)
        noise_level = st.slider("Biomechanical Hand Variation / Noise:", min_value=0.0, max_value=0.1, value=0.02, step=0.01)

        canonical = get_canonical_sign_landmarks(selected_sign)
        jitter = np.random.normal(0, noise_level, canonical.shape).astype(np.float32)
        landmarks = canonical + jitter
        feat_vec = normalize_landmarks(landmarks)

        # Base canvas
        canvas = Image.new("RGB", (320, 320), color=(20, 24, 34))
        pred_res = classifier.predict(feat_vec)
        annotated = render_hand_skeleton_hud(
            canvas, landmarks, pred_res["predicted_sign"], pred_res["confidence"]
        )
        st.image(annotated, caption="21 Hand Landmarks & Skeletal Bones", use_column_width=True)

    with col2:
        st.subheader("Classification Outcome")
        predicted = pred_res["predicted_sign"]
        conf = pred_res["confidence"] * 100

        if predicted == selected_sign:
            st.success(f"### Recognized: **{predicted}** ({conf:.1f}% confidence)")
        else:
            st.warning(f"### Recognized: **{predicted}** ({conf:.1f}% confidence)")

        st.write("#### Top Candidate Probabilities:")
        for cand in pred_res["top_candidates"]:
            st.write(f"- **{cand['sign']}**: `{cand['confidence'] * 100:.1f}%`")
            st.progress(cand["confidence"])

        info = SIGN_DICTIONARY.get(predicted, {})
        st.info(f"**Linguistic Description:** {info.get('description', '')}")

with tabs[1]:
    st.subheader("Supported Sign Dictionary (8 Core Gestures)")
    for sign_name, data in SIGN_DICTIONARY.items():
        with st.expander(f"🤟 {sign_name} (Class ID: {data['class_id']})"):
            st.write(f"**Meaning:** {data['description']}")
            st.write(f"**Fingers Extended:** {', '.join(data['fingers_extended']) if data['fingers_extended'] else 'None (Fist)'}")
            st.caption(f"**Regional Note:** {data['regional_note']}")

with tabs[2]:
    st.subheader("Model Benchmark Evaluation")
    if st.button("Run Multi-Class Benchmark"):
        X_test, y_test = generate_landmark_dataset(samples_per_sign=15, seed=999)
        preds = []
        for i in range(len(y_test)):
            p = classifier.predict(X_test[i])
            preds.append(p["predicted_class_id"])

        eval_res = SignEvaluator.evaluate(y_test, np.array(preds))
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Accuracy", f"{eval_res['accuracy'] * 100:.1f}%")
        c2.metric("Macro Precision", f"{eval_res['macro_precision'] * 100:.1f}%")
        c3.metric("Macro F1-Score", f"{eval_res['macro_f1'] * 100:.1f}%")

        st.write("#### Per-Class Performance:")
        st.json(eval_res["per_class"])

with tabs[3]:
    st.subheader("Linguistic Complexity & Dataset Limitations")
    st.markdown("""
    ### Why Sign Language Translation Is More Than Handshapes
    - **Non-Manual Markers (NMMs):** In natural Deaf communication, facial expressions, eye gaze, mouth morphemes, and head tilts indicate grammatical question forms, topicalization, and conditional clauses.
    - **Regional Variations:**
      - **ASL (American Sign Language):** Primarily one-handed manual alphabet and specific motion paths.
      - **BSL (British Sign Language):** Two-handed manual alphabet with completely distinct phonetic handshapes.
      - **Auslan (Australian Sign Language):** Closely related to BSL, but differs significantly from ASL.
    - **Continuous Motion vs. Static Pose:** Isolated hand posture classification does not capture fluid spatial transitions or sentence-level syntax.
    """)
