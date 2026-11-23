"""
Streamlit Web Application for Electricity Consumption Forecasting.
Run with: streamlit run app.py
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import streamlit as st
import pandas as pd
from dataset import generate_electricity_dataset
from model_trainer import ElectricityForecastingTrainer
from forecaster import ElectricityForecasterService


st.set_page_config(page_title="Electricity Consumption Forecasting", layout="wide")


@st.cache_resource
def get_service():
    csv_file = "electricity_consumption.csv"
    if not os.path.exists(csv_file):
        df = generate_electricity_dataset(n_days=730, output_csv=csv_file)
    else:
        df = pd.read_csv(csv_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    trainer = ElectricityForecastingTrainer()
    results = trainer.train_and_compare(df)
    service = ElectricityForecasterService(trainer=trainer)
    return service, trainer, results, df


def main():
    st.title("⚡ Electricity Consumption Forecasting Dashboard")
    st.markdown("Predict future energy demand using time-series decomposition, lagged features, and regression modeling.")

    service, trainer, results, df = get_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Forward Demand Projection")
        horizon = st.slider("Select Forecast Horizon (Days)", min_value=7, max_value=60, value=14, step=7)

        if st.button("Generate Demand Projections", type="primary"):
            fc = service.forecast_next_days(df, horizon=horizon)

            st.metric("Total Energy Needed", f"{fc['total_consumption_mwh']:.1f} MWh")
            st.metric("Projected Peak Demand", f"{fc['peak_demand_kwh']:,.1f} kWh")

            st.info(f"**Grid Status:** {fc['grid_status']}\n\n**Action:** {fc['grid_recommendation']}")

            forecast_df = pd.DataFrame({
                "Date": pd.to_datetime(fc["forecast_dates"]),
                "Projected kWh": fc["predicted_kwh"]
            }).set_index("Date")
            st.line_chart(forecast_df)

    with col_right:
        st.subheader("Time-Series Models Benchmark")
        metrics_df = pd.DataFrame(results["model_metrics"]).T[["mae", "rmse", "mape", "r2_score"]]
        st.dataframe(metrics_df.style.format({
            "mae": "{:,.2f} kWh",
            "rmse": "{:,.2f} kWh",
            "mape": "{:.2f}%",
            "r2_score": "{:.4f}"
        }))

        st.subheader("Recent Historical Demand Trend")
        recent_df = df.tail(60).set_index("timestamp")[["consumption_kwh"]]
        st.line_chart(recent_df)


if __name__ == "__main__":
    main()
