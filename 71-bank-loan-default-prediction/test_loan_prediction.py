"""
Automated unit tests for Bank Loan Default Prediction System.
"""
import unittest
import os
import tempfile
from dataset import generate_loan_dataset, FEATURE_COLUMNS
from model_trainer import LoanModelTrainer
from predictor import LoanPredictorService


class TestLoanDefaultPrediction(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.df = generate_loan_dataset(n_samples=500, seed=123, output_csv=None)
        self.trainer = LoanModelTrainer(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_dataset_generation_structure(self):
        self.assertEqual(len(self.df), 500)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, self.df.columns)
        self.assertIn("default", self.df.columns)
        self.assertEqual(self.df.isnull().sum().sum(), 0)

    def test_model_training_and_comparison(self):
        results = self.trainer.train_and_compare(self.df)
        self.assertIn(results["best_model_name"], ["Logistic Regression", "Decision Tree", "Random Forest"])
        self.assertGreater(results["best_roc_auc"], 0.60)

        for name in ["Logistic Regression", "Decision Tree", "Random Forest"]:
            self.assertIn(name, results["all_model_metrics"])
            m = results["all_model_metrics"][name]
            self.assertGreater(m["accuracy"], 0.50)
            self.assertIn("confusion_matrix", m)

    def test_low_risk_applicant_prediction(self):
        predictor = LoanPredictorService(trainer=self.trainer, db_path=self.db_path)
        # Prime borrower: high income, low DTI, high credit score, 0 defaults
        res = predictor.predict_application(
            applicant_name="Grace Hopper",
            annual_income=150000.0,
            loan_amount=10000.0,
            interest_rate=6.5,
            employment_years=10,
            debt_to_income=0.15,
            credit_score=800,
            previous_defaults=0
        )
        self.assertEqual(res["risk_category"], "Low Risk")
        self.assertLess(res["default_probability"], 0.35)
        self.assertIn("LOAN-", res["application_ref"])

    def test_high_risk_applicant_prediction(self):
        predictor = LoanPredictorService(trainer=self.trainer, db_path=self.db_path)
        # Subprime borrower: low income, high DTI, low credit score, 2 previous defaults
        res = predictor.predict_application(
            applicant_name="Risky Applicant",
            annual_income=25000.0,
            loan_amount=40000.0,
            interest_rate=24.5,
            employment_years=1,
            debt_to_income=0.65,
            credit_score=490,
            previous_defaults=2
        )
        self.assertIn(res["risk_category"], ("Medium Risk", "High Risk"))
        self.assertGreater(res["default_probability"], 0.40)

    def test_database_persistence(self):
        predictor = LoanPredictorService(trainer=self.trainer, db_path=self.db_path)
        predictor.predict_application(
            "Test Borrower", 75000.0, 15000.0, 10.0, 5, 0.25, 710, 0
        )
        apps = predictor.get_applications()
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0]["applicant_name"], "Test Borrower")


if __name__ == "__main__":
    unittest.main()
