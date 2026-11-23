"""
Unit Tests for Road Accident Severity Prediction System.
"""
import unittest
import os
from dataset import generate_accident_dataset, SEVERITY_CLASSES
from model_trainer import AccidentModelTrainer
from predictor import AccidentSeverityPredictorService
import database


class TestAccidentSeverityPrediction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_accidents.db"
        cls.test_csv = "test_accidents.csv"
        cls.df = generate_accident_dataset(n_samples=500, seed=12, output_csv=cls.test_csv)
        cls.trainer = AccidentModelTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)
        cls.service = AccidentSeverityPredictorService(trainer=cls.trainer, db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.test_db, cls.test_csv, "accident_data.csv", "accident_records.db"]:
            if os.path.exists(f):
                os.remove(f)

    def test_dataset_generation(self):
        self.assertEqual(len(self.df), 500)
        self.assertIn("severity", self.df.columns)
        self.assertIn("speed_limit", self.df.columns)
        self.assertTrue(set(self.df["severity"].unique()).issubset({0, 1, 2}))

    def test_model_metrics(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Logistic Regression", metrics)
        self.assertIn("Random Forest", metrics)
        self.assertIn("Gradient Boosting", metrics)

        for name, m in metrics.items():
            self.assertGreaterEqual(m["accuracy"], 0.55)
            self.assertGreaterEqual(m["f1_score"], 0.50)

    def test_high_risk_scenario(self):
        severe_incident = {
            "weather_condition": "Foggy",
            "road_surface": "Icy",
            "road_type": "Highway",
            "light_condition": "Darkness - no lights",
            "speed_limit": 70,
            "time_of_day": "Night",
            "vehicle_type": "Motorcycle",
            "driver_age_group": "Young (17-24)",
            "vehicles_involved": 3,
            "casualties": 3
        }
        res = self.service.evaluate_incident(severe_incident, incident_ref="ACC-SEVERE", persist=True)
        self.assertIn(res["predicted_severity"], ["Serious", "Fatal"])
        self.assertGreater(res["probabilities"]["Serious"] + res["probabilities"]["Fatal"], 0.40)
        self.assertIn("safety_recommendations", res)

    def test_low_risk_scenario(self):
        slight_incident = {
            "weather_condition": "Clear",
            "road_surface": "Dry",
            "road_type": "Single carriageway",
            "light_condition": "Daylight",
            "speed_limit": 30,
            "time_of_day": "Midday",
            "vehicle_type": "Car",
            "driver_age_group": "Adult (25-54)",
            "vehicles_involved": 1,
            "casualties": 1
        }
        res = self.service.evaluate_incident(slight_incident, incident_ref="ACC-SLIGHT", persist=True)
        self.assertEqual(res["predicted_severity"], "Slight")
        self.assertGreater(res["probabilities"]["Slight"], 0.50)

    def test_database_logging(self):
        database.save_prediction(
            incident_ref="ACC-DB-1",
            weather="Clear",
            road_surface="Dry",
            light="Daylight",
            speed_limit=30,
            vehicle_type="Car",
            predicted_severity="Slight",
            fatal_prob=0.05,
            serious_prob=0.15,
            slight_prob=0.80,
            safety_recommendations="Standard maintenance",
            db_path=self.test_db
        )
        database.save_prediction(
            incident_ref="ACC-DB-2",
            weather="Foggy",
            road_surface="Icy",
            light="Darkness - no lights",
            speed_limit=70,
            vehicle_type="Motorcycle",
            predicted_severity="Fatal",
            fatal_prob=0.75,
            serious_prob=0.20,
            slight_prob=0.05,
            safety_recommendations="Speed reduction and illumination",
            db_path=self.test_db
        )
        records = database.get_all_records(self.test_db)
        self.assertGreaterEqual(len(records), 2)
        summary = database.get_severity_summary(self.test_db)
        self.assertIn("Slight", summary)
        self.assertIn("Fatal", summary)


if __name__ == "__main__":
    unittest.main()
