"""
Streamlit Web Application for Facial Expression Recognition.
Run with: streamlit run app.py
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import streamlit as st
import cv2
import numpy as np
import pandas as pd
from dataset import create_expression_dataloaders, EXPRESSION_CLASSES, synthesize_face_image
from trainer import FERModelTrainer
from classifier import FacialExpressionClassifier


st.set_page_config(page_title="Facial Expression Recognition", layout="wide")


@st.cache_resource
def get_model():
    weights_path = "facial_expression_model.pth"
    train_loader, test_loader, _, _ = create_expression_dataloaders(samples_per_class=100, batch_size=32)
    trainer = FERModelTrainer()
    if not os.path.exists(weights_path):
        trainer.train_model(train_loader, epochs=8)
        trainer.save_weights(weights_path)
    else:
        trainer.load_weights(weights_path)
    metrics = trainer.evaluate_model(test_loader)
    classifier = FacialExpressionClassifier(weights_path=weights_path)
    return classifier, metrics


def main():
    st.title("😊 Facial Expression Recognition System")
    st.markdown("Convolutional Neural Network (CNN) application for classifying facial expressions in images.")

    classifier, metrics = get_model()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Image Input & Expression Testing")
        option = st.radio("Choose Input Mode", ["Select Preset Sample", "Upload Image"])

        if option == "Select Preset Sample":
            selected_expr = st.selectbox("Select Expression Avatar", EXPRESSION_CLASSES, index=1)
            img = synthesize_face_image(selected_expr, seed=99)
            st.image(img, caption=f"Avatar: {selected_expr}", width=180)

            if st.button("Classify Facial Expression", type="primary"):
                res = classifier.predict(img)
                st.success(f"### Predicted: **{res['predicted_expression']}** ({res['confidence_percentage']}%)")

                p_df = pd.DataFrame(list(res["probability_distribution"].items()), columns=["Expression", "Confidence %"])
                st.bar_chart(p_df.set_index("Expression"))

                st.info(f"ℹ️ {res['ethics_notice']}")

        else:
            uploaded = st.file_uploader("Upload Face Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
            if uploaded is not None:
                file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                st.image(img, caption="Uploaded Face", width=220)

                if st.button("Classify Uploaded Image", type="primary"):
                    res = classifier.predict(img)
                    st.success(f"### Predicted: **{res['predicted_expression']}** ({res['confidence_percentage']}%)")
                    p_df = pd.DataFrame(list(res["probability_distribution"].items()), columns=["Expression", "Confidence %"])
                    st.bar_chart(p_df.set_index("Expression"))
                    st.info(f"ℹ️ {res['ethics_notice']}")

    with col_right:
        st.subheader("CNN Architecture & Test Metrics")
        st.metric("Test Accuracy", f"{metrics['accuracy']*100:.1f}%")
        st.metric("Weighted F1-Score", f"{metrics['f1_score']:.4f}")

        st.subheader("Confusion Matrix")
        cm_df = pd.DataFrame(metrics["confusion_matrix"], index=EXPRESSION_CLASSES, columns=EXPRESSION_CLASSES)
        st.dataframe(cm_df)


if __name__ == "__main__":
    main()
