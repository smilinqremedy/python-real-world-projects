"""
Automated unit tests for Sign Language Recognition System.
"""
import unittest
import os
import shutil
import tempfile
import numpy as np
from PIL import Image

from sign_dictionary import SIGN_DICTIONARY, SUPPORTED_SIGNS
from hand_detector import (
    normalize_landmarks,
    get_canonical_sign_landmarks,
    generate_landmark_dataset,
    LANDMARK_NAMES,
    HAND_CONNECTIONS
)
from classifier import SignClassifier
from evaluator import SignEvaluator
from visualizer import render_hand_skeleton_hud


class TestSignLanguageRecognition(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.weights_path = os.path.join(self.test_dir, "test_weights.npz")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sign_dictionary_consistency(self):
        self.assertEqual(len(SUPPORTED_SIGNS), 8)
        for sign_name in SUPPORTED_SIGNS:
            self.assertIn(sign_name, SIGN_DICTIONARY)
            data = SIGN_DICTIONARY[sign_name]
            self.assertIn("class_id", data)
            self.assertIn("description", data)
            self.assertIn("regional_note", data)

    def test_landmark_normalization(self):
        # 21 points with 3 coordinates
        raw = np.random.randn(21, 3).astype(np.float32)
        feat = normalize_landmarks(raw)
        self.assertEqual(len(feat), 63)
        # Wrist coordinate (first 3 numbers) should be (0.0, 0.0, 0.0)
        self.assertAlmostEqual(feat[0], 0.0, places=4)
        self.assertAlmostEqual(feat[1], 0.0, places=4)
        self.assertAlmostEqual(feat[2], 0.0, places=4)

        # Invalid shape check
        with self.assertRaises(ValueError):
            normalize_landmarks(np.zeros((10, 3)))

    def test_canonical_landmark_generation(self):
        for sign_name in SUPPORTED_SIGNS:
            coords = get_canonical_sign_landmarks(sign_name)
            self.assertEqual(coords.shape, (21, 3))
            # Wrist at origin
            np.testing.assert_array_equal(coords[0], [0.0, 0.0, 0.0])

    def test_landmark_dataset_generation(self):
        X, y = generate_landmark_dataset(samples_per_sign=5, seed=42)
        total_samples = 5 * len(SUPPORTED_SIGNS)
        self.assertEqual(X.shape, (total_samples, 63))
        self.assertEqual(len(y), total_samples)
        self.assertEqual(set(y.tolist()), set(range(len(SUPPORTED_SIGNS))))

    def test_classifier_training_and_prediction(self):
        X_train, y_train = generate_landmark_dataset(samples_per_sign=15, seed=42)
        clf = SignClassifier()

        res = clf.train(X_train, y_train, epochs=10, save_path=self.weights_path)
        self.assertEqual(res["epochs"], 10)
        self.assertTrue(os.path.exists(self.weights_path))

        # Predict on a test sample
        sample_feat = X_train[0]
        pred = clf.predict(sample_feat)
        self.assertIn(pred["predicted_sign"], SUPPORTED_SIGNS)
        self.assertGreaterEqual(pred["confidence"], 0.0)
        self.assertLessEqual(pred["confidence"], 1.0)
        self.assertEqual(len(pred["top_candidates"]), 3)

        # Load weights into new classifier
        clf2 = SignClassifier()
        clf2.load_weights(self.weights_path)
        pred2 = clf2.predict(sample_feat)
        self.assertEqual(pred["predicted_sign"], pred2["predicted_sign"])
        self.assertAlmostEqual(pred["confidence"], pred2["confidence"], places=4)

    def test_evaluator_metrics(self):
        y_true = np.array([0, 1, 2, 3, 4, 5, 6, 7])
        y_pred = np.array([0, 1, 2, 3, 4, 5, 6, 7])  # Perfect predictions

        metrics = SignEvaluator.evaluate(y_true, y_pred, num_classes=8)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["macro_precision"], 1.0)
        self.assertEqual(metrics["macro_f1"], 1.0)
        self.assertEqual(len(metrics["per_class"]), 8)

    def test_visualizer_rendering(self):
        img = Image.new("RGB", (300, 300), color=(30, 30, 30))
        coords = get_canonical_sign_landmarks("Peace")
        rendered = render_hand_skeleton_hud(img, coords, "Peace", 0.95)
        self.assertEqual(rendered.size, (300, 300))


if __name__ == "__main__":
    unittest.main()
