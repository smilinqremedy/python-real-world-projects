"""
Electricity Demand Forecasting Service.
Generates multi-step future projections, peak load calculations, and energy grid advisories.
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from model_trainer import ElectricityForecastingTrainer, create_lagged_features


class ElectricityForecasterService:
    def __init__(self, trainer: ElectricityForecastingTrainer = None):
        self.trainer = trainer or ElectricityForecastingTrainer()
        if self.trainer.rf_model is None:
            self.trainer.train_and_compare()

    def forecast_next_days(self, df: pd.DataFrame, horizon: int = 14) -> Dict[str, Any]:
        """
        Iterative autoregressive multi-step forward forecasting.
        """
        history_df = df.copy().sort_values("timestamp").reset_index(drop=True)
        last_date = pd.Timestamp(history_df["timestamp"].iloc[-1])
        recent_consumption = list(history_df["consumption_kwh"].values)

        forecasts = []
        forecast_dates = []

        for step in range(1, horizon + 1):
            next_date = last_date + pd.Timedelta(days=step)
            dow = getattr(next_date, "day_of_week", next_date.dayofweek)
            is_weekend = 1 if dow >= 5 else 0
            month = next_date.month

            # Approximate seasonal temperature
            doy = getattr(next_date, "day_of_year", next_date.dayofyear)
            approx_temp = 18.0 + 12.0 * np.sin(2 * np.pi * (doy - 105) / 365)

            # Build feature vector using existing + newly predicted values
            lags = [1, 2, 7, 14, 30]
            feature_dict = {
                "temperature_c": approx_temp,
                "is_weekend": is_weekend,
                "day_of_week": dow,
                "month": month
            }
            for lag in lags:
                feature_dict[f"lag_{lag}"] = recent_consumption[-lag] if len(recent_consumption) >= lag else recent_consumption[-1]

            feature_dict["rolling_mean_7"] = np.mean(recent_consumption[-7:])
            feature_dict["rolling_std_7"] = np.std(recent_consumption[-7:])

            row_df = pd.DataFrame([feature_dict])[self.trainer.feature_columns]
            pred_kwh = float(self.trainer.rf_model.predict(row_df)[0])
            pred_kwh = round(pred_kwh, 2)

            recent_consumption.append(pred_kwh)
            forecasts.append(pred_kwh)
            forecast_dates.append(next_date.strftime("%Y-%m-%d"))

        peak_demand = max(forecasts)
        mean_demand = round(float(np.mean(forecasts)), 2)
        total_energy_mwh = round(float(np.sum(forecasts)) / 1000.0, 2)

        if peak_demand > 14500.0:
            grid_status = "High Demand Alert (Potential Grid Strain)"
            recommendation = "Engage reserve generation capacity and dispatch industrial load-shedding incentives."
        elif peak_demand > 13000.0:
            grid_status = "Moderate Demand (Normal Operations)"
            recommendation = "Standard dispatch schedule; monitor weather fluctuations."
        else:
            grid_status = "Low Demand (Off-Peak Stability)"
            recommendation = "Ideal window for scheduled substation transmission maintenance."

        return {
            "horizon_days": horizon,
            "forecast_dates": forecast_dates,
            "predicted_kwh": forecasts,
            "peak_demand_kwh": peak_demand,
            "average_daily_kwh": mean_demand,
            "total_consumption_mwh": total_energy_mwh,
            "grid_status": grid_status,
            "grid_recommendation": recommendation
        }
