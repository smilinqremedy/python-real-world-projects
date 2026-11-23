"""
House Price Prediction System - Interactive CLI
Allows data generation, model training, performance evaluation, and single property price estimation.
"""
import os
import sys
import pandas as pd
from dataset import generate_housing_dataset, FEATURE_COLUMNS
from model_trainer import HousePriceModelTrainer


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def display_model_comparison(trainer: HousePriceModelTrainer):
    results = trainer.train_and_compare()
    print_header("Model Evaluation & Comparison Results")
    print(f"{'Model':<20} | {'MAE ($)':<12} | {'RMSE ($)':<12} | {'R² Score':<10}")
    print("-" * 60)
    for model_name, metrics in results["model_metrics"].items():
        print(f"{model_name:<20} | {metrics['mae']:<12,.2f} | {metrics['rmse']:<12,.2f} | {metrics['r2_score']:<10.4f}")
    
    print("\nBest Performing Model:", results["best_model_name"])
    print(f"Best R² Score: {results['best_r2_score']:.4f}")

    print_header("Feature Importance (Random Forest)")
    for feat, imp in sorted(results["feature_importances"].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp * 40)
        print(f"  {feat:<18}: {imp:.4f} {bar}")


def interactive_prediction(trainer: HousePriceModelTrainer):
    print_header("Interactive Property Valuation Estimator")
    try:
        sqft = float(input("Enter Square Feet (e.g., 2400): ").strip() or "2400")
        bedrooms = int(input("Enter Bedrooms (1-6) (e.g., 3): ").strip() or "3")
        bathrooms = float(input("Enter Bathrooms (1.0-5.0) (e.g., 2.5): ").strip() or "2.5")
        loc_score = int(input("Enter Location Score (1-10) (e.g., 8): ").strip() or "8")
        year_built = int(input("Enter Year Built (e.g., 2012): ").strip() or "2012")
        condition = int(input("Enter Condition Rating (1-5) (e.g., 4): ").strip() or "4")
        garage = int(input("Enter Garage Spaces (0-3) (e.g., 2): ").strip() or "2")
    except ValueError:
        print("[!] Invalid input. Using sample default values.")
        sqft, bedrooms, bathrooms, loc_score, year_built, condition, garage = 2400, 3, 2.5, 8, 2012, 4, 2

    prop = {
        "square_feet": sqft,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "location_score": loc_score,
        "year_built": year_built,
        "condition_rating": condition,
        "garage_spaces": garage
    }

    price = trainer.predict_price(prop)
    print("\n------------------------------------------------------------")
    print(f" Estimated Property Valuation: ${price:,.2f}")
    print("------------------------------------------------------------")


def main():
    csv_file = "housing_records.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Generating initial dataset ({csv_file})...")
        generate_housing_dataset(n_samples=1200, output_csv=csv_file)

    trainer = HousePriceModelTrainer()
    trainer.train_and_compare()

    while True:
        print_header("House Price Prediction System")
        print("1. View Model Comparison & Metrics")
        print("2. Estimate Price for Custom Property")
        print("3. Regenerate Synthetic Dataset")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            interactive_prediction(trainer)
        elif choice == "3":
            generate_housing_dataset(n_samples=1500, output_csv=csv_file)
            print("[+] Successfully regenerated dataset.")
            trainer.train_and_compare()
        elif choice == "4":
            print("Exiting House Price Prediction System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Please try again.")


if __name__ == "__main__":
    main()
