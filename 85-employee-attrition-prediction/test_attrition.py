"""
Unit Tests for Employee Resignation Prediction System.
"""
import unittest
import os
from dataset import generate_employee_dataset
from model_trainer import EmployeeAttritionTrainer
from predictor import AttritionPredictorService
import database


class TestEmployeeAttrition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_workforce.db"
        cls.test_csv = "test_workforce.csv"
        cls.df = generate_employee_dataset(n_samples=500, seed=88, output_csv=cls.test_csv)
        cls.trainer = EmployeeAttritionTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)
        cls.service = AttritionPredictorService(trainer=cls.trainer, db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.test_db, cls.test_csv, "employee_attrition.csv", "workforce_records.db"]:
            if os.path.exists(f):
                os.remove(f)

    def test_dataset_generation(self):
        self.assertEqual(len(self.df), 500)
        self.assertIn("attrition", self.df.columns)
        self.assertIn("satisfaction_score", self.df.columns)
        self.assertTrue(set(self.df["attrition"].unique()).issubset({0, 1}))

    def test_model_benchmarks(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Logistic Regression", metrics)
        self.assertIn("Random Forest", metrics)
        self.assertIn("Gradient Boosting", metrics)

        for name, m in metrics.items():
            self.assertGreaterEqual(m["accuracy"], 0.60)
            self.assertGreaterEqual(m["roc_auc"], 0.60)
        self.assertGreaterEqual(self.results["best_f1_score"], 0.50)

    def test_high_attrition_risk_employee(self):
        high_risk_emp = {
            "employee_id": "EMP-BURNOUT",
            "department": "Engineering",
            "salary_level": "Low",
            "overtime": "Yes",
            "satisfaction_score": 0.15,
            "last_evaluation": 0.90,
            "number_of_projects": 6,
            "monthly_hours": 285,
            "tenure_years": 4,
            "promotion_last_5years": 0
        }
        res = self.service.evaluate_employee(high_risk_emp, persist=True)
        self.assertEqual(res["risk_level"], "High Risk")
        self.assertGreater(res["attrition_probability"], 0.60)
        self.assertIn("burnout", res["hr_recommendations"].lower())

    def test_low_attrition_risk_employee(self):
        low_risk_emp = {
            "employee_id": "EMP-HAPPY",
            "department": "R&D",
            "salary_level": "High",
            "overtime": "No",
            "satisfaction_score": 0.92,
            "last_evaluation": 0.75,
            "number_of_projects": 3,
            "monthly_hours": 165,
            "tenure_years": 2,
            "promotion_last_5years": 1
        }
        res = self.service.evaluate_employee(low_risk_emp, persist=True)
        self.assertEqual(res["risk_level"], "Low Risk")
        self.assertLess(res["attrition_probability"], 0.35)

    def test_database_persistence(self):
        database.save_assessment(
            employee_id="EMP-TEST1",
            department="Finance",
            tenure_years=3,
            monthly_hours=180,
            satisfaction_score=0.8,
            last_evaluation=0.7,
            promotion=0,
            salary_level="Medium",
            overtime="No",
            probability=0.15,
            risk_level="Low Risk",
            recommendations="Standard check-in",
            db_path=self.test_db
        )
        database.save_assessment(
            employee_id="EMP-TEST2",
            department="Sales",
            tenure_years=4,
            monthly_hours=270,
            satisfaction_score=0.2,
            last_evaluation=0.9,
            promotion=0,
            salary_level="Low",
            overtime="Yes",
            probability=0.88,
            risk_level="High Risk",
            recommendations="Workload intervention",
            db_path=self.test_db
        )
        records = database.get_all_assessments(self.test_db)
        self.assertGreaterEqual(len(records), 2)
        summary = database.get_attrition_summary(self.test_db)
        self.assertIn("Low Risk", summary)
        self.assertIn("High Risk", summary)


if __name__ == "__main__":
    unittest.main()
