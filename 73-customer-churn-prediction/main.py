"""
Customer Churn Prediction System - Interactive CLI
"""
import os
import sys
from dataset import generate_churn_dataset
from model_trainer import ChurnModelTrainer
from predictor import ChurnPredictorService
import database


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def display_model_comparison(trainer: ChurnModelTrainer):
    results = trainer.train_and_compare()
    print_header("Model Performance & Comparison")
    print(f"{'Model':<22} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
    print("-" * 80)
    for model_name, m in results["model_metrics"].items():
        print(f"{model_name:<22} | {m['accuracy']:<10.4f} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f} | {m['roc_auc']:<10.4f}")

    print(f"\nBest Model by F1-Score: {results['best_model_name']} (F1: {results['best_f1_score']:.4f})")

    print_header("Feature Importance (Random Forest)")
    for feat, imp in sorted(results["feature_importances"].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp * 45)
        print(f"  {feat:<22}: {imp:.4f} {bar}")


def interactive_prediction(service: ChurnPredictorService):
    print_header("Customer Churn Risk Evaluation")
    try:
        cust_id = input("Enter Customer ID (e.g. CUST-901): ").strip() or "CUST-901"
        tenure = int(input("Enter Tenure in Months (1-72) [6]: ").strip() or "6")
        print("Contract types: 1) Month-to-month  2) One year  3) Two year")
        c_choice = input("Select contract type [1]: ").strip() or "1"
        contract_map = {"1": "Month-to-month", "2": "One year", "3": "Two year"}
        contract = contract_map.get(c_choice, "Month-to-month")

        charges = float(input("Enter Monthly Charges ($) [85.5]: ").strip() or "85.5")
        tickets = int(input("Enter Recent Support Tickets [4]: ").strip() or "4")
        sec = int(input("Has Online Security? (1: Yes, 0: No) [0]: ").strip() or "0")
        sup = int(input("Has Tech Support? (1: Yes, 0: No) [0]: ").strip() or "0")
        delay = int(input("Payment Delay Days [10]: ").strip() or "10")
    except ValueError:
        print("[!] Invalid numeric input. Aborting evaluation.")
        return

    cust = {
        "customer_id": cust_id,
        "tenure_months": tenure,
        "contract_type": contract,
        "monthly_charges": charges,
        "total_charges": tenure * charges,
        "support_tickets": tickets,
        "online_security": sec,
        "tech_support": sup,
        "payment_delay_days": delay
    }

    result = service.evaluate_customer(cust, persist=True)

    print("\n" + "-" * 65)
    print(f" Customer: {result['customer_id']}")
    print(f" Churn Probability: {result['churn_percentage']} (Risk Tier: {result['risk_tier']})")
    print(f" Recommended Strategy: {result['retention_strategy']}")
    print("-" * 65)


def view_prediction_history():
    print_header("Historical Churn Predictions (SQLite)")
    records = database.get_all_predictions()
    if not records:
        print("No predictions recorded yet.")
        return

    print(f"{'ID':<4} | {'Customer':<10} | {'Tenure':<7} | {'Monthly $':<10} | {'Churn %':<10} | {'Risk Tier':<10}")
    print("-" * 65)
    for r in records[:15]:
        print(f"{r['id']:<4} | {r['customer_id']:<10} | {r['tenure_months']:<7} | {r['monthly_charges']:<10.2f} | {r['churn_probability']*100:<9.1f}% | {r['risk_tier']:<10}")


def main():
    csv_file = "customer_churn.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Initializing dataset ({csv_file})...")
        generate_churn_dataset(n_samples=1200, output_csv=csv_file)

    trainer = ChurnModelTrainer()
    trainer.train_and_compare()
    service = ChurnPredictorService(trainer=trainer)

    while True:
        print_header("Customer Churn Prediction System")
        print("1. Compare Machine Learning Models")
        print("2. Evaluate Customer Churn Risk & Retention Strategy")
        print("3. View Prediction History")
        print("4. Regenerate Synthetic Dataset")
        print("5. Exit")
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            interactive_prediction(service)
        elif choice == "3":
            view_prediction_history()
        elif choice == "4":
            generate_churn_dataset(n_samples=1500, output_csv=csv_file)
            print("[+] Dataset regenerated.")
            trainer.train_and_compare()
        elif choice == "5":
            print("Exiting Churn Prediction System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
