"""
Road Accident Severity Prediction System - Interactive CLI
"""
import os
import sys
from dataset import generate_accident_dataset
from model_trainer import AccidentModelTrainer
from predictor import AccidentSeverityPredictorService
import database


def print_header(title: str):
    print("\n" + "=" * 68)
    print(f" {title}")
    print("=" * 68)


def display_model_comparison(trainer: AccidentModelTrainer):
    results = trainer.train_and_compare()
    print_header("Model Performance & Comparison")
    print(f"{'Model':<22} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
    print("-" * 80)
    for model_name, m in results["model_metrics"].items():
        print(f"{model_name:<22} | {m['accuracy']:<10.4f} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f} | {m['roc_auc']:<10.4f}")

    print(f"\nBest Model: {results['best_model_name']} (Weighted F1: {results['best_f1_score']:.4f})")


def interactive_scenario(service: AccidentSeverityPredictorService):
    print_header("Evaluate Road Accident Risk Scenario")
    try:
        ref = input("Enter Incident Ref [ACC-2024-USR]: ").strip() or "ACC-2024-USR"
        print("Weather: 1) Clear  2) Rainy  3) Foggy  4) Snowing")
        w_map = {"1": "Clear", "2": "Rainy", "3": "Foggy", "4": "Snowing"}
        weather = w_map.get(input("Select Weather [1]: ").strip() or "1", "Clear")

        print("Road Surface: 1) Dry  2) Wet  3) Icy  4) Flooded")
        s_map = {"1": "Dry", "2": "Wet", "3": "Icy", "4": "Flooded"}
        surface = s_map.get(input("Select Road Surface [1]: ").strip() or "1", "Dry")

        print("Lighting: 1) Daylight  2) Darkness - lights lit  3) Darkness - no lights")
        l_map = {"1": "Daylight", "2": "Darkness - lights lit", "3": "Darkness - no lights"}
        light = l_map.get(input("Select Lighting [1]: ").strip() or "1", "Daylight")

        speed = int(input("Enter Speed Limit (30, 40, 50, 60, 70) [50]: ").strip() or "50")

        print("Vehicle Type: 1) Car  2) Motorcycle  3) Truck  4) Bus  5) Bicycle")
        v_map = {"1": "Car", "2": "Motorcycle", "3": "Truck", "4": "Bus", "5": "Bicycle"}
        vtype = v_map.get(input("Select Vehicle Type [1]: ").strip() or "1", "Car")

        vehicles = int(input("Number of Vehicles Involved [2]: ").strip() or "2")
        casualties = int(input("Number of Casualties [1]: ").strip() or "1")
    except ValueError:
        print("[!] Invalid input. Using standard scenario values.")
        ref, weather, surface, light, speed, vtype, vehicles, casualties = "ACC-DEFAULT", "Clear", "Dry", "Daylight", 40, "Car", 2, 1

    incident = {
        "weather_condition": weather,
        "road_surface": surface,
        "road_type": "Single carriageway",
        "light_condition": light,
        "speed_limit": speed,
        "time_of_day": "Evening Rush",
        "vehicle_type": vtype,
        "driver_age_group": "Adult (25-54)",
        "vehicles_involved": vehicles,
        "casualties": casualties
    }

    res = service.evaluate_incident(incident, incident_ref=ref, persist=True)

    print("\n" + "-" * 68)
    print(f" Incident: {res['incident_ref']}")
    print(f" Predicted Severity: {res['predicted_severity'].upper()}")
    probs = res["probabilities"]
    print(f" Probabilities -> Slight: {probs['Slight']*100:.1f}% | Serious: {probs['Serious']*100:.1f}% | Fatal: {probs['Fatal']*100:.1f}%")
    print(f" Safety Recommendations: {res['safety_recommendations']}")
    print(f" Note: {res['limitations_notice']}")
    print("-" * 68)


def view_history():
    print_header("Historical Accident Evaluations (SQLite)")
    records = database.get_all_records()
    if not records:
        print("No evaluations recorded yet.")
        return

    print(f"{'ID':<4} | {'Ref':<14} | {'Weather':<8} | {'Speed':<6} | {'Vehicle':<10} | {'Severity':<10}")
    print("-" * 68)
    for r in records[:15]:
        print(f"{r['id']:<4} | {r['incident_ref']:<14} | {r['weather_condition']:<8} | {r['speed_limit']:<6} | {r['vehicle_type']:<10} | {r['predicted_severity']:<10}")

    stats = database.get_severity_summary()
    print(f"\nSummary Totals -> Slight: {stats['Slight']} | Serious: {stats['Serious']} | Fatal: {stats['Fatal']}")


def main():
    csv_file = "accident_data.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Initializing road accident historical records ({csv_file})...")
        generate_accident_dataset(n_samples=1500, output_csv=csv_file)

    trainer = AccidentModelTrainer()
    trainer.train_and_compare()
    service = AccidentSeverityPredictorService(trainer=trainer)

    while True:
        print_header("Road Accident Severity Prediction System")
        print("1. Compare Classification Models")
        print("2. Evaluate Road Accident Scenario")
        print("3. View Historical Evaluations (SQLite)")
        print("4. Regenerate Synthetic Dataset")
        print("5. Exit")
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            interactive_scenario(service)
        elif choice == "3":
            view_history()
        elif choice == "4":
            generate_accident_dataset(n_samples=2000, output_csv=csv_file)
            print("[+] Accident dataset regenerated.")
            trainer.train_and_compare()
        elif choice == "5":
            print("Exiting Road Accident Analytics System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
