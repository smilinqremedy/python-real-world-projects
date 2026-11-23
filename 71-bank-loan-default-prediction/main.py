"""
Command-Line Interface for Bank Loan Default Prediction System.
"""
import sys
from model_trainer import LoanModelTrainer
from predictor import LoanPredictorService
from dataset import generate_loan_dataset


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_model_comparison(results: dict):
    print("\n" + "-" * 75)
    print(f"{'MODEL':<22} | {'ACCURACY':<8} | {'PRECISION':<9} | {'RECALL':<8} | {'F1':<8} | {'ROC-AUC':<8}")
    print("-" * 75)
    for model_name, m in results["all_model_metrics"].items():
        print(f"{model_name:<22} | {m['accuracy']:<8.4f} | {m['precision']:<9.4f} | {m['recall']:<8.4f} | {m['f1_score']:<8.4f} | {m['roc_auc']:<8.4f}")
    print("-" * 75)
    print(f"Best Performing Model: {results['best_model_name']} (ROC-AUC: {results['best_roc_auc']})")


def main():
    trainer = LoanModelTrainer()
    predictor = None

    while True:
        print_banner("Bank Loan Default Prediction System")
        print("1. Train & Compare Classification Models")
        print("2. Predict Loan Default Risk for Applicant")
        print("3. Generate & Ingest 1,000 Historical Loan Training Records")
        print("4. View Underwriting Queue & Recent Applications")
        print("0. Exit")

        choice = input("\nSelect an option [0-4]: ").strip()

        if choice == "1":
            print("\nTraining Logistic Regression, Decision Tree, and Random Forest...")
            res = trainer.train_and_compare()
            display_model_comparison(res)
            predictor = LoanPredictorService(trainer=trainer)

        elif choice == "2":
            if predictor is None:
                print("Initializing predictor engine...")
                predictor = LoanPredictorService(trainer=trainer)

            print_banner("Applicant Credit Assessment")
            name = input("Applicant Full Name: ").strip() or "Sample Applicant"
            try:
                income = float(input("Annual Income ($): ").strip())
                loan_amt = float(input("Requested Loan Amount ($): ").strip())
                rate = float(input("Interest Rate (%) [e.g. 11.5]: ").strip())
                emp_yrs = int(input("Employment Duration (Years): ").strip())
                dti = float(input("Debt-to-Income Ratio (DTI, e.g. 0.32): ").strip())
                credit = int(input("Credit Score (FICO 300 - 850): ").strip())
                prev_def = int(input("Number of Previous Defaults [0]: ").strip() or "0")

                res = predictor.predict_application(
                    applicant_name=name,
                    annual_income=income,
                    loan_amount=loan_amt,
                    interest_rate=rate,
                    employment_years=emp_yrs,
                    debt_to_income=dti,
                    credit_score=credit,
                    previous_defaults=prev_def
                )

                print("\n" + "-" * 60)
                print(f"APPLICATION REF:    {res['application_ref']}")
                print(f"APPLICANT:          {res['applicant_name']}")
                print(f"DEFAULT LIKELIHOOD: {res['default_probability_percentage']} (Prob: {res['default_probability']})")
                print(f"RISK CATEGORY:      [{res['risk_category'].upper()}]")
                print(f"EVALUATED BY:       {res['model_used']}")
                print(f"RECOMMENDATION:     {res['recommendation']}")
                print(f"\n{res['disclaimer']}")
                print("-" * 60)
            except Exception as e:
                print(f"Error during prediction: {e}")

        elif choice == "3":
            csv_path = "loan_records.csv"
            df = generate_loan_dataset(n_samples=1200, output_csv=csv_path)
            print(f"\nSuccessfully generated {len(df)} loan records saved to: '{csv_path}'.")
            print("Default class distribution:")
            print(df["default"].value_counts(normalize=True).round(3))

        elif choice == "4":
            if predictor is None:
                predictor = LoanPredictorService(trainer=trainer)
            print_banner("Recent Applications")
            apps = predictor.get_applications(limit=10)
            if not apps:
                print("No loan applications logged yet.")
            else:
                for a in apps:
                    print(f"[{a['application_ref']}] {a['applicant_name']} | Loan: ${a['loan_amount']:,.2f} | Score: {a['credit_score']} | Risk: {a['risk_category']} ({a['default_probability'] * 100:.1f}%)")

        elif choice == "0":
            print("Exiting Loan Prediction System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()
