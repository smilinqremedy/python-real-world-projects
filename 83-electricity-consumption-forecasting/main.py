"""
Electricity Consumption Forecasting System - Interactive CLI
"""
import os
import sys
import pandas as pd
from dataset import generate_electricity_dataset
from model_trainer import ElectricityForecastingTrainer
from forecaster import ElectricityForecasterService


def print_header(title: str):
    print("\n" + "=" * 68)
    print(f" {title}")
    print("=" * 68)


def display_model_comparison(trainer: ElectricityForecastingTrainer):
    results = trainer.train_and_compare()
    print_header("Time-Series Model Performance & Benchmark")
    print(f"{'Model':<26} | {'MAE (kWh)':<12} | {'RMSE (kWh)':<12} | {'MAPE (%)':<10} | {'R² Score':<10}")
    print("-" * 75)
    for model_name, m in results["model_metrics"].items():
        print(f"{model_name:<26} | {m['mae']:<12.2f} | {m['rmse']:<12.2f} | {m['mape']:<10.2f}% | {m['r2_score']:<10.4f}")

    print_header("Top Predictive Lagged Features (Random Forest)")
    for feat, imp in list(results["feature_importances"].items())[:7]:
        bar = "█" * int(imp * 45)
        print(f"  {feat:<18}: {imp:.4f} {bar}")


def generate_forward_projection(service: ElectricityForecasterService, df: pd.DataFrame):
    print_header("Generate Forward Electricity Demand Forecast")
    try:
        horizon = int(input("Enter forecast horizon in days (7, 14, 30) [14]: ").strip() or "14")
    except ValueError:
        horizon = 14

    result = service.forecast_next_days(df, horizon=horizon)

    print("\n" + "-" * 68)
    print(f" Forecast Horizon: {result['horizon_days']} Days")
    print(f" Total Projected Energy: {result['total_consumption_mwh']} MWh")
    print(f" Peak Daily Demand:     {result['peak_demand_kwh']:,.2f} kWh")
    print(f" Average Daily Demand:  {result['average_daily_kwh']:,.2f} kWh")
    print(f" Grid Operating Status: {result['grid_status']}")
    print(f" Advisory Action:       {result['grid_recommendation']}")
    print("-" * 68)

    print("\nDay-by-Day Forecast Schedule:")
    print(f"{'Date':<14} | {'Projected Consumption (kWh)':<28}")
    print("-" * 45)
    for dt, val in zip(result["forecast_dates"], result["predicted_kwh"]):
        print(f"{dt:<14} | {val:>15,.2f} kWh")


def main():
    csv_file = "electricity_consumption.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Initializing historical consumption series ({csv_file})...")
        df = generate_electricity_dataset(n_days=730, output_csv=csv_file)
    else:
        df = pd.read_csv(csv_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    trainer = ElectricityForecastingTrainer()
    trainer.train_and_compare(df)
    service = ElectricityForecasterService(trainer=trainer)

    while True:
        print_header("Electricity Consumption Forecasting System")
        print("1. Compare Time-Series Forecasting Models")
        print("2. Generate Out-of-Sample Demand Projections")
        print("3. Regenerate Synthetic Historical Time-Series")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            generate_forward_projection(service, df)
        elif choice == "3":
            df = generate_electricity_dataset(n_days=730, output_csv=csv_file)
            print("[+] Time-series records regenerated.")
            trainer.train_and_compare(df)
        elif choice == "4":
            print("Exiting Electricity Forecasting System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
