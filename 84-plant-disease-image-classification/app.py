"""
Streamlit Web Application for Plant Disease Image Classification.
Run with: streamlit run app.py
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import streamlit as st
import cv2
import numpy as np
import pandas as pd
from dataset import create_plant_dataloaders, DISEASE_CLASSES, synthesize_leaf_image
from trainer import PlantDiseaseTrainer
from classifier import PlantDiseaseClassifier


st.set_page_config(page_title="Plant Disease Image Classification", layout="wide")


@st.cache_resource
def get_model():
    weights_path = "plant_disease_model.pth"
    train_loader, test_loader, _, _ = create_plant_dataloaders(samples_per_class=100, batch_size=32)
    trainer = PlantDiseaseTrainer()
    if not os.path.exists(weights_path):
        trainer.train_model(train_loader, epochs=8)
        trainer.save_weights(weights_path)
    else:
        trainer.load_weights(weights_path)
    metrics = trainer.evaluate_model(test_loader)
    classifier = PlantDiseaseClassifier(weights_path=weights_path)
    return classifier, metrics


def main():
    st.title("🌿 Plant Disease Image Classification System")
    st.markdown("Computer Vision application for early crop leaf pathology detection, treatment advisories, and agricultural education.")

    classifier, metrics = get_model()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Leaf Image Diagnosis")
        mode = st.radio("Select Image Source", ["Preset Disease Sample", "Upload Leaf Photo"])

        if mode == "Preset Disease Sample":
            chosen_disease = st.selectbox("Select Leaf Pathology", DISEASE_CLASSES, index=1)
            img = synthesize_leaf_image(chosen_disease, seed=777)
            st.image(img, caption=f"Sample: {chosen_disease}", width=200)

            if st.button("Diagnose Leaf Sample", type="primary"):
                res = classifier.predict(img)
                st.success(f"### Detected: **{res['predicted_disease']}** ({res['confidence_percentage']}%)")

                p_df = pd.DataFrame(list(res["probability_distribution"].items()), columns=["Disease", "Confidence %"])
                st.bar_chart(p_df.set_index("Disease"))

                st.info(f"**Symptoms:** {res['symptoms']}")
                st.warning(f"**Recommended Treatment:** {res['treatment_recommendation']}")
                st.caption(f"ℹ️ {res['specialist_disclaimer']}")

        else:
            uploaded = st.file_uploader("Upload Leaf Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
            if uploaded is not None:
                file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                st.image(img, caption="Uploaded Leaf", width=220)

                if st.button("Diagnose Uploaded Leaf", type="primary"):
                    res = classifier.predict(img)
                    st.success(f"### Detected: **{res['predicted_disease']}** ({res['confidence_percentage']}%)")
                    st.info(f"**Treatment:** {res['treatment_recommendation']}")
                    st.caption(f"ℹ️ {res['specialist_disclaimer']}")

    with col_right:
        st.subheader("CNN Model Architecture & Evaluation")
        st.metric("Test Accuracy", f"{metrics['accuracy']*100:.1f}%")
        st.metric("Weighted F1-Score", f"{metrics['f1_score']:.4f}")

        st.subheader("Confusion Matrix")
        cm_df = pd.DataFrame(metrics["confusion_matrix"], index=DISEASE_CLASSES, columns=DISEASE_CLASSES)
        st.dataframe(cm_df)


if __name__ == "__main__":
    main()
