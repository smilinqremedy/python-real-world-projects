"""
Streamlit Web Application for House Price Prediction.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from dataset import generate_housing_dataset, FEATURE_COLUMNS
from model_trainer import HousePriceModelTrainer


st.set_page_config(page_title="House Price Prediction Dashboard", layout="wide")

@st.cache_resource
def get_trained_models():
    trainer = HousePriceModelTrainer()
    metrics = trainer.train_and_compare()
    return trainer, metrics


def main():
    st.title("🏡 House Price Prediction System")
    st.markdown("Predict property values using machine learning algorithms trained on historical housing data.")

    trainer, training_results = get_trained_models()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Property Features")
        sqft = st.slider("Square Feet", min_value=800, max_value=5500, value=2200, step=50)
        bedrooms = st.selectbox("Bedrooms", options=[1, 2, 3, 4, 5, 6], index=2)
        bathrooms = st.slider("Bathrooms", min_value=1.0, max_value=5.0, value=2.5, step=0.5)
        location_score = st.slider("Location Score (1: Low, 10: Prime)", min_value=1, max_value=10, value=7)
        year_built = st.slider("Year Built", min_value=1965, max_value=2024, value=2010)
        condition_rating = st.select_slider("Condition Rating (1-5)", options=[1, 2, 3, 4, 5], value=4)
        garage_spaces = st.selectbox("Garage Spaces", options=[0, 1, 2, 3], index=2)

        input_data = {
            "square_feet": sqft,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "location_score": location_score,
            "year_built": year_built,
            "condition_rating": condition_rating,
            "garage_spaces": garage_spaces
        }

        if st.button("Predict Property Value", type="primary"):
            pred_price = trainer.predict_price(input_data)
            st.success(f"### Estimated Price: ${pred_price:,.2f}")

    with col_right:
        st.subheader("Model Benchmark & Evaluation")
        metrics_df = pd.DataFrame(training_results["model_metrics"]).T
        st.dataframe(metrics_df.style.format({
            "mae": "${:,.2f}",
            "mse": "{:,.0f}",
            "rmse": "${:,.2f}",
            "r2_score": "{:.4f}"
        }))

        st.subheader("Feature Importance (Random Forest)")
        feat_df = pd.DataFrame(
            list(training_results["feature_importances"].items()),
            columns=["Feature", "Importance"]
        ).sort_values("Importance", ascending=True)
        st.bar_chart(feat_df.set_index("Feature"))


if __name__ == "__main__":
    main()
