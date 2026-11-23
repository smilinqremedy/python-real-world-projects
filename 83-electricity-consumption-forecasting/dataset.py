"""
Electricity Consumption Time-Series Dataset Generator.
Generates multi-year chronological daily electricity consumption records with trend, seasonality, and temperature drivers.
"""
import numpy as np
import pandas as pd


def generate_electricity_dataset(n_days: int = 730, seed: int = 42, output_csv: str = "electricity_consumption.csv") -> pd.DataFrame:
    """
    Generates n_days of daily electricity consumption (kWh) starting from 2023-01-01.
    Includes:
    - Base demand: ~12,000 kWh/day
    - Upward linear trend (+1.5 kWh/day)
    - Weekly seasonality (weekdays +1,200 kWh, weekends -800 kWh)
    - Annual seasonality (summer cooling peak in July/Aug, winter heating peak in Jan/Dec)
    - Temperature correlation (U-shaped demand)
    - Random Gaussian noise
    """
    np.random.seed(seed)
    start_date = pd.Timestamp("2023-01-01")
    dates = [start_date + pd.Timedelta(days=i) for i in range(n_days)]

    day_of_year = np.array([getattr(d, "day_of_year", d.dayofyear) for d in dates])
    day_of_week = np.array([getattr(d, "day_of_week", d.dayofweek) for d in dates])
    is_weekend = np.array([1 if dow >= 5 else 0 for dow in day_of_week])

    # Temperature simulation (°C): seasonal cycle around 18°C
    temperature = 18.0 + 12.0 * np.sin(2 * np.pi * (day_of_year - 105) / 365) + np.random.normal(0, 2.5, n_days)

    # Base + Trend
    base_demand = 12500.0 + (np.arange(n_days) * 1.8)

    # Weekly pattern: lower on Saturday/Sunday
    weekly_effect = np.where(is_weekend == 1, -1100.0, 450.0)

    # Annual seasonal pattern: peaks in mid-winter (day 15) and mid-summer (day 200)
    annual_effect = 1200.0 * np.cos(2 * np.pi * (day_of_year - 15) / 365) + 800.0 * np.sin(2 * np.pi * day_of_year / 182.5)

    # Temperature effect: U-shape heating/cooling
    temp_effect = np.maximum(0, 16.0 - temperature) * 65.0 + np.maximum(0, temperature - 24.0) * 85.0

    noise = np.random.normal(0, 180.0, n_days)

    consumption = base_demand + weekly_effect + annual_effect + temp_effect + noise
    consumption = np.round(np.clip(consumption, 5000, None), 2)

    df = pd.DataFrame({
        "timestamp": dates,
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "consumption_kwh": consumption,
        "temperature_c": np.round(temperature, 1),
        "is_weekend": is_weekend,
        "day_of_week": day_of_week,
        "month": [d.month for d in dates]
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
