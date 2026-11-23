"""
Streamlit Web Dashboard for Road Accident Severity Analysis.
Run with: streamlit run app.py
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import streamlit as st
import pandas as pd
from dataset import generate_accident_dataset, SEVERITY_CLASSES
from model_trainer import AccidentModelTrainer
from predictor import AccidentSeverityPredictorService
import database


st.set_page_config(page_title="Road Accident Severity Prediction", layout="wide")


@st.cache_resource
def get_service():
    trainer = AccidentModelTrainer()
    results = trainer.train_and_compare()
    service = AccidentSeverityPredictorService(trainer=trainer)
    return service, results


def main():
    st.title("🚦 Road Accident Severity Prediction & Risk Analysis")
    st.markdown("Transportation analytics application identifying critical road hazard patterns and predicting multi-class accident severity outcomes.")

    service, results = get_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Accident Scenario Conditions")
        ref = st.text_input("Incident Reference", value="ACC-SIM-701")
        weather = st.selectbox("Weather Condition", ["Clear", "Rainy", "Foggy", "Snowing"], index=0)
        surface = st.selectbox("Road Surface", ["Dry", "Wet", "Icy", "Flooded"], index=0)
        road_type = st.selectbox("Road Type", ["Single carriageway", "Dual carriageway", "Roundabout", "Highway"], index=0)
        light = st.selectbox("Lighting", ["Daylight", "Darkness - lights lit", "Darkness - no lights"], index=0)
        speed_limit = st.select_slider("Speed Limit (mph)", options=[30, 40, 50, 60, 70], value=50)
        time_of_day = st.selectbox("Time of Day", ["Morning Rush", "Midday", "Evening Rush", "Night"], index=2)
        vehicle_type = st.selectbox("Primary Vehicle Involved", ["Car", "Motorcycle", "Truck", "Bus", "Bicycle"], index=0)
        driver_age = st.selectbox("Driver Age Group", ["Young (17-24)", "Adult (25-54)", "Senior (55+)"], index=1)
        vehicles = st.slider("Total Vehicles Involved", min_value=1, max_value=5, value=2)
        casualties = st.slider("Total Casualties", min_value=1, max_value=4, value=1)

        if st.button("Predict Severity & Safety Risks", type="primary"):
            incident = {
                "weather_condition": weather,
                "road_surface": surface,
                "road_type": road_type,
                "light_condition": light,
                "speed_limit": speed_limit,
                "time_of_day": time_of_day,
                "vehicle_type": vehicle_type,
                "driver_age_group": driver_age,
                "vehicles_involved": vehicles,
                "casualties": casualties
            }
            res = service.evaluate_incident(incident, incident_ref=ref, persist=True)

            color_badge = {"Slight": "🟢", "Serious": "🟡", "Fatal": "🔴"}
            st.markdown(f"### Predicted Severity: {color_badge.get(res['predicted_severity'], '')} **{res['predicted_severity'].upper()}**")

            probs = res["probabilities"]
            p_df = pd.DataFrame(list(probs.items()), columns=["Severity", "Probability"])
            st.bar_chart(p_df.set_index("Severity"))

            st.warning(f"**Safety Engineering Interventions:**\n\n{res['safety_recommendations']}")
            st.caption(f"ℹ️ {res['limitations_notice']}")

    with col_right:
        st.subheader("Model Benchmark & Evaluation")
        metrics_df = pd.DataFrame(results["model_metrics"]).T[["accuracy", "precision", "recall", "f1_score", "roc_auc"]]
        st.dataframe(metrics_df.style.format("{:.4f}"))

        st.subheader("Recent Evaluations in SQLite")
        recent = database.get_all_records(limit=10)
        if recent:
            st.dataframe(pd.DataFrame(recent)[["incident_ref", "weather_condition", "speed_limit", "vehicle_type", "predicted_severity"]])


if __name__ == "__main__":
    main()
