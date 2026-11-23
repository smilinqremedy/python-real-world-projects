"""
Unit Tests for House Price Prediction System.
"""
import unittest
import os
import pandas as pd
from dataset import generate_housing_dataset, FEATURE_COLUMNS
from model_trainer import HousePriceModelTrainer


class TestHousePricePrediction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_csv = "test_housing_data.csv"
        cls.df = generate_housing_dataset(n_samples=500, seed=123, output_csv=cls.test_csv)
        cls.trainer = HousePriceModelTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_csv):
            os.remove(cls.test_csv)
        if os.path.exists("housing_records.csv"):
            os.remove("housing_records.csv")

    def test_dataset_generation(self):
        self.assertEqual(len(self.df), 500)
        for col in FEATURE_COLUMNS + ["price"]:
            self.assertIn(col, self.df.columns)
        self.assertTrue((self.df["price"] > 0).all())
        self.assertTrue((self.df["square_feet"] >= 800).all())

    def test_model_training_and_comparison(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Linear Regression", metrics)
        self.assertIn("Decision Tree", metrics)
        self.assertIn("Random Forest", metrics)

        # Check performance metrics exist and R2 is reasonably high (> 0.70)
        for name, m in metrics.items():
            self.assertIn("mae", m)
            self.assertIn("rmse", m)
            self.assertIn("r2_score", m)
            self.assertGreater(m["r2_score"], 0.70)

    def test_feature_importance(self):
        importances = self.results["feature_importances"]
        self.assertEqual(len(importances), len(FEATURE_COLUMNS))
        # Square feet and location score should be influential
        self.assertGreater(importances["square_feet"], 0.05)
        self.assertGreater(importances["location_score"], 0.05)

    def test_single_prediction(self):
        sample_prop = {
            "square_feet": 2500,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "location_score": 8,
            "year_built": 2015,
            "condition_rating": 4,
            "garage_spaces": 2
        }
        price = self.trainer.predict_price(sample_prop)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 100000.0)
        self.assertLess(price, 2000000.0)


if __name__ == "__main__":
    unittest.main()
