"""
Employee Resignation Prediction System - Interactive CLI
"""
import os
import sys
from dataset import generate_employee_dataset
from model_trainer import EmployeeAttritionTrainer
from predictor import AttritionPredictorService
import database


def print_header(title: str):
    print("\n" + "=" * 68)
    print(f" {title}")
    print("=" * 68)


def display_model_comparison(trainer: EmployeeAttritionTrainer):
    results = trainer.train_and_compare()
    print_header("Model Performance & Comparison")
    print(f"{'Model':<22} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
    print("-" * 80)
    for model_name, m in results["model_metrics"].items():
        print(f"{model_name:<22} | {m['accuracy']:<10.4f} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f} | {m['roc_auc']:<10.4f}")

    print(f"\nBest Model: {results['best_model_name']} (F1: {results['best_f1_score']:.4f})")

    print_header("Top Influential Factors for Turnover (Random Forest)")
    for feat, imp in sorted(results["feature_importances"].items(), key=lambda x: x[1], reverse=True)[:8]:
        bar = "█" * int(imp * 50)
        print(f"  {feat:<25}: {imp:.4f} {bar}")


def interactive_evaluation(service: AttritionPredictorService):
    print_header("Assess Employee Turnover Risk Profile")
    try:
        emp_id = input("Enter Employee ID [EMP-2041]: ").strip() or "EMP-2041"
        dept = input("Department (Engineering, Sales, Support, HR, Marketing) [Engineering]: ").strip() or "Engineering"
        sat = float(input("Job Satisfaction Score (0.1 to 1.0) [0.35]: ").strip() or "0.35")
        eval_score = float(input("Last Performance Evaluation (0.3 to 1.0) [0.82]: ").strip() or "0.82")
        hours = int(input("Average Monthly Working Hours (130-310) [260]: ").strip() or "260")
        tenure = int(input("Years of Service / Tenure [4]: ").strip() or "4")
        promo = int(input("Promoted in Last 5 Years? (1: Yes, 0: No) [0]: ").strip() or "0")
        salary = input("Salary Level (Low, Medium, High) [Low]: ").strip() or "Low"
        ot = input("Frequently Works Overtime? (Yes, No) [Yes]: ").strip() or "Yes"
    except ValueError:
        print("[!] Invalid input. Using sample values.")
        emp_id, dept, sat, eval_score, hours, tenure, promo, salary, ot = "EMP-DEF", "Engineering", 0.35, 0.82, 260, 4, 0, "Low", "Yes"

    emp = {
        "employee_id": emp_id,
        "department": dept,
        "salary_level": salary,
        "overtime": ot,
        "satisfaction_score": sat,
        "last_evaluation": eval_score,
        "number_of_projects": 5,
        "monthly_hours": hours,
        "tenure_years": tenure,
        "promotion_last_5years": promo
    }

    res = service.evaluate_employee(emp, persist=True)

    print("\n" + "-" * 68)
    print(f" Employee ID: {res['employee_id']}")
    print(f" Resignation Risk: {res['risk_level']} (Probability: {res['attrition_percentage']})")
    print(f" HR Action Plan: {res['hr_recommendations']}")
    print("-" * 68)


def view_history():
    print_header("Historical Attrition Assessments (SQLite)")
    records = database.get_all_assessments()
    if not records:
        print("No employee evaluations logged yet.")
        return

    print(f"{'ID':<4} | {'Emp ID':<10} | {'Dept':<12} | {'Hours':<6} | {'Risk Level':<12} | {'Prob':<6}")
    print("-" * 68)
    for r in records[:15]:
        print(f"{r['id']:<4} | {r['employee_id']:<10} | {r['department']:<12} | {r['monthly_hours']:<6} | {r['risk_level']:<12} | {r['attrition_probability']*100:<5.1f}%")

    stats = database.get_attrition_summary()
    print(f"\nWorkforce Totals -> Low: {stats['Low Risk']} | Medium: {stats['Medium Risk']} | High: {stats['High Risk']}")


def main():
    csv_file = "employee_attrition.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Initializing historical workforce records ({csv_file})...")
        generate_employee_dataset(n_samples=1500, output_csv=csv_file)

    trainer = EmployeeAttritionTrainer()
    trainer.train_and_compare()
    service = AttritionPredictorService(trainer=trainer)

    while True:
        print_header("Employee Resignation Prediction System")
        print("1. Compare Workforce Classification Models")
        print("2. Assess Employee Resignation Risk")
        print("3. View Historical Assessments (SQLite)")
        print("4. Regenerate Synthetic Dataset")
        print("5. Exit")
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            interactive_evaluation(service)
        elif choice == "3":
            view_history()
        elif choice == "4":
            generate_employee_dataset(n_samples=2000, output_csv=csv_file)
            print("[+] Workforce dataset refreshed.")
            trainer.train_and_compare()
        elif choice == "5":
            print("Exiting Employee Attrition Analytics System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
