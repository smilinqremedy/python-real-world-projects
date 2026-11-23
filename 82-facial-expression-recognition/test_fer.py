"""
Unit Tests for Facial Expression Recognition System.
"""
import unittest
import os
import cv2
import numpy as np
import torch
from dataset import synthesize_face_image, create_expression_dataloaders, EXPRESSION_CLASSES
from model import FacialExpressionCNN
from trainer import FERModelTrainer
from classifier import FacialExpressionClassifier


class TestFacialExpressionRecognition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weights_path = "test_fer_model.pth"
        cls.train_loader, cls.test_loader, _, _ = create_expression_dataloaders(samples_per_class=40, batch_size=16, seed=42)
        cls.trainer = FERModelTrainer(num_classes=5)
        cls.trainer.train_model(cls.train_loader, epochs=5)
        cls.trainer.save_weights(cls.weights_path)
        cls.classifier = FacialExpressionClassifier(weights_path=cls.weights_path)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.weights_path, "facial_expression_model.pth", "sample_test_face.png"]:
            if os.path.exists(f):
                os.remove(f)

    def test_image_synthesis_and_preprocessing(self):
        img = synthesize_face_image("Happy", seed=10)
        self.assertEqual(img.shape, (48, 48))
        self.assertEqual(img.dtype, np.uint8)

        tensor = self.classifier.preprocess_image(img)
        self.assertEqual(tensor.shape, (1, 1, 48, 48))
        self.assertTrue((tensor >= 0.0).all() and (tensor <= 1.0).all())

    def test_cnn_forward_pass(self):
        model = FacialExpressionCNN(num_classes=5)
        dummy_input = torch.randn(4, 1, 48, 48)
        output = model(dummy_input)
        self.assertEqual(output.shape, (4, 5))

    def test_evaluation_metrics(self):
        metrics = self.trainer.evaluate_model(self.test_loader)
        self.assertIn("accuracy", metrics)
        self.assertIn("f1_score", metrics)
        self.assertIn("confusion_matrix", metrics)
        self.assertGreater(metrics["accuracy"], 0.70)
        self.assertGreater(metrics["f1_score"], 0.70)

    def test_inference_and_ethics_notice(self):
        sample_img = synthesize_face_image("Surprise", seed=99)
        res = self.classifier.predict(sample_img)
        self.assertIn(res["predicted_expression"], EXPRESSION_CLASSES)
        self.assertGreater(res["confidence_percentage"], 20.0)
        self.assertIn("ethics_notice", res)
        self.assertIn("psychological", res["ethics_notice"].lower())


if __name__ == "__main__":
    unittest.main()
