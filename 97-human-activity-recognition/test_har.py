"""
Automated unit tests for Human Activity Recognition System.
"""
import unittest
import os
import shutil
import tempfile
import numpy as np

from dataset import (
    ACTIVITIES,
    CHANNELS,
    create_sliding_windows,
    generate_synthetic_har_dataset,
    load_subject_data
)
from model import HAR1DCNN
from trainer import HARTrainer
from evaluator import HAREvaluator
from visualizer import render_sensor_waveform_image, format_confusion_matrix_ascii


class TestHumanActivityRecognition(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.weights_path = os.path.join(self.test_dir, "test_har_weights.npz")

        # Generate mini synthetic dataset
        self.dataset_dir = os.path.join(self.test_dir, "dataset")
        generate_synthetic_har_dataset(self.dataset_dir, num_subjects=2, samples_per_activity=100, seed=42)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sliding_window_segmentation(self):
        # 200 timesteps of 6 channels
        data = np.random.randn(200, 6).astype(np.float32)
        labels = np.array([0] * 100 + [1] * 100, dtype=int)

        X_win, y_win = create_sliding_windows(data, labels, window_size=64, step_size=32)
        # Expected windows: (200 - 64) // 32 + 1 = 5 windows
        self.assertEqual(X_win.shape, (5, 6, 64))
        self.assertEqual(len(y_win), 5)
        self.assertEqual(y_win[0], 0)
        self.assertEqual(y_win[-1], 1)

    def test_dataset_generation_and_loading(self):
        sub1_dir = os.path.join(self.dataset_dir, "subject_01")
        self.assertTrue(os.path.exists(sub1_dir))

        data, labels = load_subject_data(sub1_dir)
        self.assertEqual(data.shape[1], 6)
        self.assertEqual(len(data), len(labels))
        self.assertEqual(len(set(labels)), 6)

    def test_1d_cnn_forward_and_prediction(self):
        model = HAR1DCNN(in_channels=6, window_size=64, num_classes=6, seed=42)
        dummy_x = np.random.randn(3, 6, 64).astype(np.float32)

        logits, probs = model.forward(dummy_x)
        self.assertEqual(logits.shape, (3, 6))
        self.assertEqual(probs.shape, (3, 6))

        for row in probs:
            self.assertAlmostEqual(float(np.sum(row)), 1.0, places=4)

        preds, _ = model.predict(dummy_x)
        self.assertEqual(len(preds), 3)

        # Weight saving & loading
        model.save_weights(self.weights_path)
        self.assertTrue(os.path.exists(self.weights_path))

        model2 = HAR1DCNN(in_channels=6, window_size=64)
        model2.load_weights(self.weights_path)
        _, probs2 = model2.forward(dummy_x)
        np.testing.assert_allclose(probs, probs2, rtol=1e-5)

    def test_trainer_and_subject_leakage_isolation(self):
        d1, l1 = load_subject_data(os.path.join(self.dataset_dir, "subject_01"))
        d2, l2 = load_subject_data(os.path.join(self.dataset_dir, "subject_02"))

        # Train on subject 1, validate strictly on subject 2 (prevent cross-subject data leakage)
        X_train, y_train = create_sliding_windows(d1, l1, window_size=64, step_size=20)
        X_val, y_val = create_sliding_windows(d2, l2, window_size=64, step_size=32)

        trainer = HARTrainer()
        res = trainer.train(X_train, y_train, X_val, y_val, epochs=2, save_path=self.weights_path)

        self.assertEqual(res["epochs"], 2)
        self.assertTrue(os.path.exists(self.weights_path))
        self.assertIn("accuracy", res["validation_metrics"])

    def test_evaluator_and_visualizer(self):
        y_true = np.array([0, 1, 2, 3, 4, 5])
        y_pred = np.array([0, 1, 2, 3, 4, 5])

        metrics = HAREvaluator.evaluate(y_true, y_pred, num_classes=6)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["macro_f1"], 1.0)

        ascii_table = format_confusion_matrix_ascii(metrics["confusion_matrix"])
        self.assertIn("Walking", ascii_table)

        # Waveform rendering
        dummy_window = np.random.randn(6, 64).astype(np.float32)
        wf_img = render_sensor_waveform_image(dummy_window)
        self.assertEqual(wf_img.size, (500, 240))


if __name__ == "__main__":
    unittest.main()
