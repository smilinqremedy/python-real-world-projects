"""
Unit Tests for Customer Churn Prediction System.
"""
import unittest
import os
from dataset import generate_churn_dataset, FEATURE_COLUMNS
from model_trainer import ChurnModelTrainer
from predictor import ChurnPredictorService
import database


class TestCustomerChurnPrediction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_churn.db"
        cls.test_csv = "test_churn.csv"
        cls.df = generate_churn_dataset(n_samples=600, seed=99, output_csv=cls.test_csv)
        cls.trainer = ChurnModelTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)
        cls.service = ChurnPredictorService(trainer=cls.trainer, db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.test_db, cls.test_csv, "customer_churn.csv", "churn_records.db"]:
            if os.path.exists(f):
                os.remove(f)

    def test_dataset_generation(self):
        self.assertEqual(len(self.df), 600)
        for col in FEATURE_COLUMNS + ["churn"]:
            self.assertIn(col, self.df.columns)
        self.assertIn(self.df["churn"].nunique(), [1, 2])

    def test_model_metrics(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Logistic Regression", metrics)
        self.assertIn("Decision Tree", metrics)
        self.assertIn("Random Forest", metrics)

        for name, m in metrics.items():
            self.assertGreater(m["accuracy"], 0.60)
            self.assertGreaterEqual(m["f1_score"], 0.35)
            self.assertGreater(m["roc_auc"], 0.60)

    def test_high_risk_prediction(self):
        high_risk_customer = {
            "customer_id": "CUST-HIGH",
            "tenure_months": 2,
            "contract_type": "Month-to-month",
            "monthly_charges": 110.0,
            "total_charges": 220.0,
            "support_tickets": 6,
            "online_security": 0,
            "tech_support": 0,
            "payment_delay_days": 18
        }
        res = self.service.evaluate_customer(high_risk_customer, persist=True)
        self.assertIn(res["risk_tier"], ["Moderate", "High"])
        self.assertGreater(res["churn_probability"], 0.40)
        self.assertIn("discount", res["retention_strategy"].lower() + res["retention_strategy"].lower())

    def test_low_risk_prediction(self):
        low_risk_customer = {
            "customer_id": "CUST-LOW",
            "tenure_months": 60,
            "contract_type": "Two year",
            "monthly_charges": 35.0,
            "total_charges": 2100.0,
            "support_tickets": 0,
            "online_security": 1,
            "tech_support": 1,
            "payment_delay_days": 0
        }
        res = self.service.evaluate_customer(low_risk_customer, persist=True)
        self.assertEqual(res["risk_tier"], "Low")
        self.assertLess(res["churn_probability"], 0.40)

    def test_database_logging(self):
        database.save_prediction(
            customer_id="CUST-TEST1",
            tenure_months=12,
            contract_type="One year",
            monthly_charges=50.0,
            support_tickets=1,
            payment_delay_days=0,
            churn_probability=0.20,
            risk_tier="Low",
            retention_strategy="Standard",
            db_path=self.test_db
        )
        database.save_prediction(
            customer_id="CUST-TEST2",
            tenure_months=2,
            contract_type="Month-to-month",
            monthly_charges=90.0,
            support_tickets=4,
            payment_delay_days=10,
            churn_probability=0.85,
            risk_tier="High",
            retention_strategy="Discount offer",
            db_path=self.test_db
        )
        records = database.get_all_predictions(self.test_db)
        self.assertGreaterEqual(len(records), 2)
        summary = database.get_risk_summary(self.test_db)
        self.assertIn("Low", summary)
        self.assertIn("High", summary)


if __name__ == "__main__":
    unittest.main()
