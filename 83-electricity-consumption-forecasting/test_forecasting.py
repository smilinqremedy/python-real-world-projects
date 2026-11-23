"""
Unit Tests for Electricity Consumption Forecasting System.
"""
import unittest
import os
import pandas as pd
from dataset import generate_electricity_dataset
from model_trainer import ElectricityForecastingTrainer, create_lagged_features
from forecaster import ElectricityForecasterService


class TestElectricityForecasting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_csv = "test_electricity.csv"
        cls.df = generate_electricity_dataset(n_days=400, seed=55, output_csv=cls.test_csv)
        cls.trainer = ElectricityForecastingTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)
        cls.service = ElectricityForecasterService(trainer=cls.trainer)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.test_csv, "electricity_consumption.csv"]:
            if os.path.exists(f):
                os.remove(f)

    def test_dataset_generation(self):
        self.assertEqual(len(self.df), 400)
        self.assertIn("consumption_kwh", self.df.columns)
        self.assertIn("timestamp", self.df.columns)
        self.assertTrue((self.df["consumption_kwh"] > 0).all())

    def test_lagged_feature_engineering(self):
        lagged_df = create_lagged_features(self.df)
        self.assertIn("lag_1", lagged_df.columns)
        self.assertIn("lag_7", lagged_df.columns)
        self.assertIn("rolling_mean_7", lagged_df.columns)
        self.assertFalse(lagged_df.isnull().values.any())

    def test_model_performance(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Baseline (Persistence)", metrics)
        self.assertIn("Random Forest (Lagged)", metrics)

        rf_metrics = metrics["Random Forest (Lagged)"]
        self.assertLess(rf_metrics["mape"], 10.0)  # MAPE under 10%
        self.assertGreaterEqual(rf_metrics["r2_score"], 0.55)

    def test_forward_forecasting(self):
        fc = self.service.forecast_next_days(self.df, horizon=7)
        self.assertEqual(len(fc["predicted_kwh"]), 7)
        self.assertEqual(len(fc["forecast_dates"]), 7)
        self.assertGreater(fc["peak_demand_kwh"], 5000.0)
        self.assertIn("grid_status", fc)


if __name__ == "__main__":
    unittest.main()
