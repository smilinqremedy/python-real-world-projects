"""
Unit and integration tests for AI-Based Medical Image Classification System.
"""
import unittest
import os
import shutil
import tempfile
import numpy as np
from PIL import Image

from dataset import (
    validate_image_file,
    preprocess_image,
    generate_sample_medical_dataset,
    split_dataset,
    CLASSES
)
from model import MedicalCNN
from evaluator import MedicalEvaluator
from trainer import MedicalModelTrainer
from classifier import MedicalClassifierService, CLINICAL_SAFETY_DISCLAIMER
import database


class TestMedicalClassification(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_medical.db")
        self.weights_path = os.path.join(self.test_dir, "test_weights.npz")

        # Generate mini synthetic dataset
        self.dataset_dir = os.path.join(self.test_dir, "dataset")
        self.records = generate_sample_medical_dataset(
            self.dataset_dir,
            samples_per_class=6,
            img_size=(64, 64),
            seed=42
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_image_validation_and_preprocessing(self):
        valid_img_path = self.records["Normal"][0]
        self.assertTrue(validate_image_file(valid_img_path))

        # Test preprocessing output dimensions and normalization
        tensor = preprocess_image(valid_img_path, target_size=(64, 64))
        self.assertEqual(tensor.shape, (1, 64, 64))
        self.assertTrue(np.isfinite(tensor).all())

        # Test invalid non-existent file
        self.assertFalse(validate_image_file("non_existent_file.png"))
        with self.assertRaises(ValueError):
            preprocess_image("non_existent_file.png")

        # Test corrupted/empty file
        empty_file = os.path.join(self.test_dir, "empty.png")
        with open(empty_file, "wb") as f:
            f.write(b"")
        self.assertFalse(validate_image_file(empty_file))
        with self.assertRaises(ValueError):
            preprocess_image(empty_file)

    def test_sample_dataset_generation_and_splitting(self):
        self.assertIn("Normal", self.records)
        self.assertIn("Pneumonia", self.records)
        self.assertEqual(len(self.records["Normal"]), 6)
        self.assertEqual(len(self.records["Pneumonia"]), 6)

        train, val, test = split_dataset(self.records, train_ratio=0.6, val_ratio=0.2, seed=42)
        total_split = len(train) + len(val) + len(test)
        self.assertEqual(total_split, 12)
        self.assertTrue(len(train) > 0)
        self.assertTrue(len(val) > 0)
        self.assertTrue(len(test) > 0)

    def test_cnn_forward_and_prediction(self):
        cnn = MedicalCNN(in_channels=1, num_classes=2, seed=42)
        dummy_input = np.random.randn(2, 1, 64, 64).astype(np.float32)

        logits, probs = cnn.forward(dummy_input)
        self.assertEqual(logits.shape, (2, 2))
        self.assertEqual(probs.shape, (2, 2))

        # Softmax probabilities must sum to 1.0 per sample
        for row in probs:
            self.assertAlmostEqual(float(np.sum(row)), 1.0, places=4)

        preds, _ = cnn.predict(dummy_input)
        self.assertEqual(len(preds), 2)
        for p in preds:
            self.assertIn(p, [0, 1])

        # Test saving and loading weights
        cnn.save_weights(self.weights_path)
        self.assertTrue(os.path.exists(self.weights_path))

        cnn2 = MedicalCNN(in_channels=1, num_classes=2)
        cnn2.load_weights(self.weights_path)
        _, probs2 = cnn2.forward(dummy_input)
        np.testing.assert_allclose(probs, probs2, rtol=1e-5)

    def test_evaluator_metrics(self):
        y_true = [0, 1, 0, 1, 1, 0]
        y_pred = [0, 1, 0, 0, 1, 1]

        cm = MedicalEvaluator.compute_confusion_matrix(y_true, y_pred, num_classes=2)
        self.assertEqual(cm.shape, (2, 2))

        metrics = MedicalEvaluator.evaluate(y_true, y_pred, num_classes=2)
        self.assertIn("accuracy", metrics)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("f1_score", metrics)
        self.assertIn("confusion_matrix", metrics)
        self.assertEqual(metrics["total_samples"], 6)

    def test_training_pipeline(self):
        train_data, val_data, _ = split_dataset(self.records, train_ratio=0.7, val_ratio=0.3)
        trainer = MedicalModelTrainer()
        res = trainer.train(train_data, val_data, epochs=2, save_weights_path=self.weights_path)

        self.assertEqual(res["epochs"], 2)
        self.assertTrue(os.path.exists(self.weights_path))
        self.assertIn("accuracy", res["validation_metrics"])

    def test_database_logging_and_history(self):
        sample_img = self.records["Normal"][0]
        log_id = database.log_prediction(
            image_name="test_xray.png",
            file_path=sample_img,
            predicted_class="Normal",
            confidence_score=0.92,
            normal_prob=0.92,
            pneumonia_prob=0.08,
            db_path=self.db_path,
            user_notes="Routine test"
        )
        self.assertGreater(log_id, 0)

        history = database.get_prediction_history(limit=10, db_path=self.db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["image_name"], "test_xray.png")
        self.assertEqual(history[0]["predicted_class"], "Normal")
        self.assertEqual(history[0]["disclaimer_acknowledged"], 1)

    def test_classifier_service_with_disclaimer(self):
        sample_img = self.records["Pneumonia"][0]
        service = MedicalClassifierService(db_path=self.db_path)
        res = service.classify_image(sample_img, user_notes="Unit test screening")

        self.assertTrue(res["success"])
        self.assertIn(res["predicted_class"], CLASSES)
        self.assertIn("Normal", res["probabilities"])
        self.assertIn("Pneumonia", res["probabilities"])
        self.assertTrue(res["is_experimental"])
        self.assertEqual(res["disclaimer"], CLINICAL_SAFETY_DISCLAIMER)

        # Invalid file handling
        bad_res = service.classify_image("missing.png")
        self.assertFalse(bad_res["success"])
        self.assertEqual(bad_res["disclaimer"], CLINICAL_SAFETY_DISCLAIMER)


if __name__ == "__main__":
    unittest.main()
